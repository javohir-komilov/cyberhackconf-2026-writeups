FROM maven:3.9-eclipse-temurin-11 AS build
WORKDIR /app
COPY pom.xml .
# Download dependencies first (layer caching)
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

FROM eclipse-temurin:11-jre-alpine
WORKDIR /app

# Install common tools (useful after RCE)
# NOTE: do NOT install netcat-openbsd — it would replace BusyBox nc which has -e support
RUN apk add --no-cache \
    curl \
    wget \
    bash \
    iputils \
    nmap \
    bind-tools \
    procps \
    coreutils \
    findutils \
    grep \
    vim \
    python3 \
    py3-pip

# Create uploads directory for CTF RCE output
RUN mkdir -p /vaultpass_uploads && chmod 777 /vaultpass_uploads

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
