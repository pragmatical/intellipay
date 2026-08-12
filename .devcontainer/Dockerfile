FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends zsh-autosuggestions \
    && rm -rf /var/lib/apt/lists/*

COPY intellipay.zsh /etc/zsh/intellipay.zsh

RUN printf '\nsource /etc/zsh/intellipay.zsh\n' >> /etc/zsh/zshrc            