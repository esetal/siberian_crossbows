class CreateCrossbows < ActiveRecord::Migration[5.1]
  def change
    create_table :crossbows do |t|
      t.string :brand
      t.string :model
      t.text :description
      t.string :condition
      t.string :title
      t.string :secret
      t.decimal :price, precision: 5, scale: 2, default: 0

      t.timestamps
    end
  end
end
