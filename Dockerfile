FROM ruby:2.5.3
RUN apt-get update -qq && apt-get install -y nodejs
RUN mkdir /app
WORKDIR /app
ENV RAILS_ENV=development
COPY src/Gemfile /app/Gemfile
COPY src/Gemfile.lock /app/Gemfile.lock
RUN bundle install
COPY /src /app

# Expose port

EXPOSE 3000
