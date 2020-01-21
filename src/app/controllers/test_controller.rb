class TestController < ApplicationController
  def index
    render file: "#{Rails.root}/README.md", content_type: "text/plain"
  end
end

