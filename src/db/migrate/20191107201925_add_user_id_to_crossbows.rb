class AddUserIdToCrossbows < ActiveRecord::Migration[5.1]
  def change
    add_column :crossbows, :user_id, :integer
  end
end
