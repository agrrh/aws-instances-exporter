# Info

# Usage

```
docker build . -t agrrh/aws-instances-exporter:dev
docker run -d --name aws-instances-exporter \
  -e AWS_INSTANCES_PERIOD=600 \
  -e AWS_INSTANCES_REGIONS=us-east-1,eu-central-1 \
  -p 4321:8000 \
  --restart unless-stopped \
  agrrh/aws-instances-exporter:dev

http 0.0.0.0:4321
```
