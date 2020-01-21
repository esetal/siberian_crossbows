# This file should contain all the record creation needed to seed the database with its default values.
# The data can then be loaded with the rails db:seed command (or created alongside the database with db:setup).
#
# Examples:
#
#   movies = Movie.create([{ name: 'Star Wars' }, { name: 'Lord of the Rings' }])
#   Character.create(name: 'Luke', movie: movies.first)

user = User.new(
  id: 2,
  name: "Pozhiloi Sibiryak",
  email: "31337@gmail.com",
  password: "password",
  password_confirmation: "password"
)
user.save!

Crossbow.create!([{
  title: "Excalibur Axe 340",
  brand: "Excalibur",
  model: "Axe 340",
  description: "The AXE 340 brings best in class performance, Value, Accuracy, and lifetime warranty at an unmatchable price. Just like an AXE this crossbow is designed to take care of all your needs, capable of taking down any animal in any situation. With an aluminum frame, anti dry-fire, premium trigger, and our R.E.D. Suppressors, this crossbow package is dependable companion for beginners and pros alike. And it’s all tied together with the premium Dead Zone Scope. If you’re looking for workhorse crossbow, with lifetime dependability at an affordable price, look no further than the AXE 340 from Excalibur. ",
  condition: "Excellent",
  secret: "murder weapon :‑/",
  price: "2999",
  image: Rails.root.join("app/assets/images/crossbow1.jpg").open,
  user_id: user.id
}])