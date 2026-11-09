FROM eclipse-temurin:21-jdk-jammy

RUN apt-get update && \
    apt-get install -y python3 python3-pip python-is-python3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    streamlit

RUN mkdir -p bin && \
    javac \
    -sourcepath src \
    -cp "bin:jars/*:jars/commons-math3-3.5/commons-math3-3.5.jar" \
    -d bin \
    src/org/fog/test/perfeval/DrainGuardFogApp.java

RUN chmod +x start.sh

EXPOSE 8501

CMD ["./start.sh"]
