class CrossbowsController < ApplicationController
  before_action :set_crossbow, only: [:show, :edit, :update, :destroy]
  before_action :authenticate_user!, except: [:index, :show]

  # GET /crossbows
  # GET /crossbows.json
  def index 
  ## TODO: add searchbox in index page
    if(params.has_key?(:search))
      @crossbows = Crossbow.all.where("title like '$#{params[:search]}$'")
    else
      @crossbows = Crossbow.all.order("created_at desc")
    end
  end

  # GET /crossbows/1
  # GET /crossbows/1.json
  def show
  end

  # GET /crossbows/new
  def new
    @crossbow = current_user.crossbows.build
  end

  # GET /crossbows/1/edit
  def edit
  end

  # POST /crossbows
  # POST /crossbows.json
  def create
    @crossbow = current_user.crossbows.build(crossbow_params)
    respond_to do |format|
      if @crossbow.save
        format.html { redirect_to @crossbow, notice: 'Crossbow was successfully created.' }
        format.json { render :show, status: :created, location: @crossbow }
      else
        format.html { render :new }
        format.json { render json: @crossbow.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /crossbows/1
  # PATCH/PUT /crossbows/1.json
  def update
    respond_to do |format|
      if @crossbow.update(crossbow_params)
        format.html { redirect_to @crossbow, notice: 'Crossbow was successfully updated.' }
        format.json { render :show, status: :ok, location: @crossbow }
      else
        format.html { render :edit }
        format.json { render json: @crossbow.errors, status: :unprocessable_entity }
      end
    end
  end

  # DELETE /crossbows/1
  # DELETE /crossbows/1.json
  def destroy
    @crossbow.destroy
    respond_to do |format|
      format.html { redirect_to crossbows_url, notice: 'Crossbow was successfully destroyed.' }
      format.json { head :no_content }
    end
  end

  private
    # Use callbacks to share common setup or constraints between actions.
    def set_crossbow
      @crossbow = Crossbow.find(params[:id])
    end

    # Never trust parameters from the scary internet, only allow the white list through.
    def crossbow_params
      params.require(:crossbow).permit(:brand, :model, :description, :condition, :title, :secret, :price, :image)
    end
end
