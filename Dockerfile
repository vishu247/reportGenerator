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


# Install GitHub CLI based on architecture
RUN if [ "$(uname -m)" = "x86_64" ]; then \
        wget https://github.com/cli/cli/releases/download/v2.45.0/gh_2.45.0_linux_amd64.deb && \
        dpkg -i gh_2.45.0_linux_amd64.deb; \
        export ARCH_VALUE="amd64"; \
    elif [ "$(uname -m)" = "AArch64" ]; then \
        wget https://github.com/cli/cli/releases/download/v2.45.0/gh_2.45.0_linux_arm64.deb && \
        dpkg -i gh_2.45.0_linux_arm64.deb; \
        export ARCH_VALUE="arm64"; \
    else \
        echo "Unsupported architecture"; \
        exit 1; \
    fi


CMD ["python3","script.py"]

