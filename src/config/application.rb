require_relative 'boot'

require 'rails/all'

# Require the gems listed in Gemfile, including any gems
# you've limited to :test, :development, or :production.
Bundler.require(*Rails.groups)

module SCM
  class Application < Rails::Application
    # Initialize configuration defaults for originally generated Rails version.
    config.web_console.whitelisted_ips = '172.0.0.0/8'
    config.load_defaults 5.1
    config.encoding = "BINARY"
    config.serve_static_assets = false
	config.assets.compile = true
	js_prefix    = 'app/assets/javascripts/'
	style_prefix = 'app/assets/stylesheets/'
	
	javascripts = Dir["#{js_prefix}**/*.js"].map      { |x| x.gsub(js_prefix,    '') }
	css         = Dir["#{style_prefix}**/*.css"].map  { |x| x.gsub(style_prefix, '') }
	scss        = Dir["#{style_prefix}**/*.scss"].map { |x| x.gsub(style_prefix, '') }
	
	config.assets.precompile = (javascripts + css + scss)

    # Settings in config/environments/* take precedence over those specified here.
    # Application configuration should go into files in config/initializers
    # -- all .rb files in that directory are automatically loaded.
  end
end
