FROM python

COPY ./script.py .

ENV GIT_HUB_TOKEN=
ENV PROJECT_NODE_ID=
ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=
ENV AWS_REGION=
ENV MAIL=
ENV SENDER=
ENV REPO=
ENV PROJECT=
ENV LIMIT=

RUN apt update
RUN pip3 install requests boto3 load_dotenv pyyaml jinja2 
RUN wget https://github.com/cli/cli/releases/download/v2.45.0/gh_2.45.0_linux_amd64.deb
RUN dpkg -i gh_2.45.0_linux_amd64.deb


CMD ["python3","script.py"]

