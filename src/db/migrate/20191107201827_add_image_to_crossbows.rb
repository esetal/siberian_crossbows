class AddImageToCrossbows < ActiveRecord::Migration[5.1]
  def change
    add_column :crossbows, :image, :string
  end
end
