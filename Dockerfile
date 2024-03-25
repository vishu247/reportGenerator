FROM python

COPY ./script.py .

RUN apt update
RUN pip3 install requests boto3 load_dotenv pyyaml jinja2 


# Install GitHub CLI based on architecture
RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && echo $arch &&  wget  https://github.com/cli/cli/releases/download/v2.45.0/gh_2.45.0_linux_${arch}.deb && \
        dpkg -i gh_2.45.0_linux_${arch}.deb;

CMD ["python3","script.py"]
