class LineItem < ApplicationRecord
  belongs_to :crossbow
  belongs_to :cart

  def total_price
    crossbow.price.to_i * quantity.to_i
  end
end
