FROM ghcr.io/reyery/daysim:release AS daysim

FROM ghcr.io/reyery/cea/usr:latest AS usr

FROM mambaorg/micromamba:2.0 AS cea
LABEL org.opencontainers.image.source=https://github.com/architecture-building-systems/CityEnergyAnalyst

USER root
# create directory for projects and set MAMBA_USER as owner
RUN mkdir -p /project && chown $MAMBA_USER /project

USER $MAMBA_USER
# create conda environment and configure matplotlib
# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml /tmp/conda-lock.yml
RUN micromamba config set extract_threads 1 \
    && micromamba install --name base --yes --file /tmp/conda-lock.yml \
    && micromamba clean --all --yes \
    && mkdir -p ~/.config/matplotlib \
    && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc \
    && rm -f /tmp/conda-lock.yml

# active environment to install CEA
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# install cea and clean up
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN pip install /tmp/cea && rm -rf /tmp/cea

# Copy Daysim from build stage
COPY --from=daysim / /Daysim

# Copy USR binary
COPY --from=usr /USR /USR

# write config files
RUN cea-config write --general:project /project/reference-case-open \
    && cea-config write --general:scenario-name baseline \
    && cea-config write --radiation:daysim-bin-directory /Daysim \
    && cea-config write --radiation:usr-bin-directory /USR \
    && cea-config write --server:host 0.0.0.0 \
    # create dummy project folder
    && mkdir -p /project/reference-case-open

# Expose dashboard port
EXPOSE 5050

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD cea dashboard
