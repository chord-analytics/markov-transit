FROM ubuntu:18.04
RUN apt update && apt upgrade -y && \
    apt install python3.7-dev -y --no-install-recommends && apt install python3-pip -y --no-install-recommends && \
    apt install python3-setuptools -y --no-install-recommends && apt install cmake -y --no-install-recommends && \
    apt install git -y --no-install-recommends && apt install make -y --no-install-recommends && \
    apt install g++ -y --no-install-recommends

COPY requirements.txt .
RUN python3.7 -m pip install -r requirements.txt

RUN git clone https://github.com/pybind/pybind11.git
RUN mkdir /pybind11/build; cd /pybind11/build; cmake ..; make -j2; make install

COPY truncated_norm_cpp truncated_norm_cpp
RUN python3.7 -m pip install truncated_norm_cpp/

# matplotlib config (used by benchmark)
RUN mkdir -p /root/.config/matplotlib
RUN echo "backend : Agg" > /root/.config/matplotlib/matplotlibrc
# alias python3.7 as python
RUN echo 'alias python=python3.7' >> ~/.bashrc

