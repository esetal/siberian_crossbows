Rails.application.routes.draw do
  resources :test
  resources :line_items
  resources :carts
  resources :crossbows
  devise_for :users, controllers: {
    registrations: 'registrations'
  }
  root 'crossbows#index'

  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
end
