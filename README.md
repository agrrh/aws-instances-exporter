# Info

Simple exporter to provide AWS instance details.

This is probably better to setup with CloudWatch, but there's always a reason for inventing a bicycle.

# Usage

```bash
# build image
docker build . -t agrrh/aws-instances-exporter:dev

# provide credentials
cp credentials{.example,}.py
${EDITOR} credentials.py

# run container
docker run -d --name aws-instances-exporter \
  -e AWS_INSTANCES_PERIOD=600 \
  -e AWS_INSTANCES_REGIONS=us-east-1,eu-central-1 \
  -p 4321:8000 \
  -v $(pwd)/credentials.py:/app/credentials.py \
  --restart unless-stopped \
  agrrh/aws-instances-exporter:dev

# access metrics
http 0.0.0.0:4321
```