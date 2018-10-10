FROM tiagopeixoto/graph-tool
RUN useradd -ms /bin/bash sciradar
#COPY --chown=sciradar . /home/sciradar
WORKDIR /home/sciradar
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN pacman -S python-pip --noconfirm
RUN pip install -r requirements.txt
RUN sed -i 's/def echo(message=None, file=None, nl=True, err=False, color=None):/def echo(message=None, file=sys.stdout, nl=True, err=False, color=None):/g' /lib/python3.6/site-packages/click/utils.py
RUN sed -i 's/def secho(text, file=None, nl=True, err=False, color=None, \*\*styles):/def secho(text, file=sys.stdout, nl=True, err=False, color=None, \*\*styles):/g' /lib/python3.6/site-packages/click/termui.py
USER sciradar
CMD ["jupyter", "notebook", "--ip", "0.0.0.0"]
