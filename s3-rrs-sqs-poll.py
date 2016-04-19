#!/usr/bin/python
import boto
import sys
import boto.sqs
import json
import time
import os
import pprint

# Usage
#./restoreobject src_bucket_name target_bucket_name

s3 = boto.connect_s3()
src_bucket_name = sys.argv[1]
target_bucket_name = sys.argv[2]

if not s3.lookup(target_bucket_name):
  print "Target Bucket not found ... Creating"

target_bucket_name = s3.get_bucket(target_bucket_name)

src_bucket_name = s3.get_bucket(src_bucket_name)
if not src_bucket_name:
  print "Source Bucket not found ... Exiting"
  sys.exit(1)

sqs = boto.sqs.connect_to_region("us-east-1")
devops = sqs.get_queue('cat_queue')

from boto.sqs.message import RawMessage
devops.set_message_class(RawMessage)

result = devops.get_messages()

if len(result) == 0:
  print "No messages available... Exiting"
  sys.exit(1)

#read the message body
m = result[0]
body = m.get_body()
decoded_message = json.loads(body)
decoded_message = json.loads(decoded_message["Message"])


print decoded_message["Key"]

# read the file from trhe src bucket
src_key = src_bucket_name.get_key(decoded_message["Key"])
src_key.get_contents_to_filename("images/" + decoded_message["Key"])

#apply the black filter to the image
os.system("convert images/"+decoded_message["Key"] + " -monochrome " + decoded_message["Key"])

#upload the image back to the location it was before it was lost
from boto.s3.key import Key
key = Key(target_bucket_name)
key.key = decoded_message["Key"]
key.set_contents_from_filename(decoded_message["Key"])

print "Your lost file has been automatically recreated and uploaded to its proper location"

devops.delete_message(m)

