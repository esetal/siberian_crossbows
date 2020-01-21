module CrossbowsHelper

  def crossbow_author(crossbow)
    user_signed_in? && current_user.id == crossbow.user_id
  end

end
