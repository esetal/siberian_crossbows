require 'test_helper'

class CrossbowsControllerTest < ActionDispatch::IntegrationTest
  setup do
    @crossbow = crossbows(:one)
  end

  test "should get index" do
    get crossbows_url
    assert_response :success
  end

  test "should get new" do
    get new_crossbow_url
    assert_response :success
  end

  test "should create crossbow" do
    assert_difference('Crossbow.count') do
      post crossbows_url, params: { crossbow: { brand: @crossbow.brand, condition: @crossbow.condition, description: @crossbow.description, model: @crossbow.model, price: @crossbow.price, title: @crossbow.title } }
    end

    assert_redirected_to crossbow_url(Crossbow.last)
  end

  test "should show crossbow" do
    get crossbow_url(@crossbow)
    assert_response :success
  end

  test "should get edit" do
    get edit_crossbow_url(@crossbow)
    assert_response :success
  end

  test "should update crossbow" do
    patch crossbow_url(@crossbow), params: { crossbow: { brand: @crossbow.brand, condition: @crossbow.condition, description: @crossbow.description, model: @crossbow.model, price: @crossbow.price, title: @crossbow.title } }
    assert_redirected_to crossbow_url(@crossbow)
  end

  test "should destroy crossbow" do
    assert_difference('Crossbow.count', -1) do
      delete crossbow_url(@crossbow)
    end

    assert_redirected_to crossbows_url
  end
end
