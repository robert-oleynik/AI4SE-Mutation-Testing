FROM fedora:40

RUN dnf install --assumeyes python3 python3-pip dnf-plugins-core
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/fedora39/x86_64/cuda-fedora39.repo
RUN dnf module install --assumeyes nvidia-driver:latest-dkms
RUN pip3 install torch transformers pandas

RUN dnf install --assumeyes git

COPY src/ /project/src
COPY pyproject.toml /project
RUN pip3 install /project

ENTRYPOINT [ "python3", "-m", "mutator" ]
