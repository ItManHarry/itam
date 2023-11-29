USE [FlexNet]
GO
/****** Object:  UserDefinedFunction [dbo].[DI_FN_GetEquipRecipeItemList]    Script Date: 2022/12/7 14:50:52 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO




/*
    2020-11-27, KCE
	    도장장 관련 MaterialNo 추가 및 WorkCenter 조건절 삭제
*/

ALTER FUNCTION [dbo].[DI_FN_GetEquipRecipeItemList]
(	
	@Facility		NVARCHAR(80),
	@Equipment		NVARCHAR(80),
	@WorkCenter		NVARCHAR(80)
)
RETURNS @RetunTable TABLE( 
	Facility			NVARCHAR(40) 
	,Equipment			NVARCHAR(80)
	,WorkCenter			NVARCHAR(40)
	,ProductionLineNo	NVARCHAR(40)
	,WipOrderNo			NVARCHAR(40)
	,WipOrderType		SMALLINT
	,OprSequenceNo		NVARCHAR(40)
	,ModelCode			NVARCHAR(40)
	,ModelName			NVARCHAR(100)
	,SerialNo			NVARCHAR(40)
	,SequenceNo			NVARCHAR(40)
	,MaterialNo			NVARCHAR(80)	
	,Item				NVARCHAR(255)
	,ItemValue			NVARCHAR(255)
) 
AS
BEGIN
	
	INSERT INTO @RetunTable
	SELECT
		 WRI.Facility
		,WRI.Equipment
		,WRI.WorkCenter
		,WRI.ProductionLineNo
		,WRI.WipOrderNo
		,WRI.WipOrderType
		,WRI.OprSequenceNo
		,WRI.ModelCode
		,WRI.ModelName
		,WRI.SerialNo
		,WRI.SequenceNo
		,WRI.MaterialNo		
		,WRI.Item
		,WRI.ItemValue
	FROM DI_CO_MI_EQUIPMENT_WORK_RECIPE_ITEM WRI,
		 DI_CO_MI_EQUIPMENT_WORK_RECIPE WR
   WHERE WR.WipOrderNo   = WRI.WipOrderNo
     AND WR.WipOrderType = WRI.WipOrderType
	 AND WR.Facility     = WRI.Facility
	 AND WR.Equipment    = WRI.Equipment
	 AND WR.Equipment    = WRI.Equipment
	 AND WR.RecipeNo     = WRI.RecipeNo
     AND WR.Facility     = @Facility
     AND WR.Equipment    = @Equipment
      AND WR.SendStatus    = 0;

	IF @@ROWCOUNT = 0
	BEGIN
		INSERT INTO @RetunTable
		SELECT
			 WR.Facility
			,WR.Equipment
			,WR.WorkCenter
			,WR.ProductionLineNo
			,WR.WipOrderNo
			,WR.WipOrderType
			,WR.OprSequenceNo
			,WR.ModelCode
			,WR.ModelName
			,WR.SerialNo
			,WR.SequenceNo
			,WR.MaterialNo			
			,NULL Item
			,NULL ItemValue
		FROM DI_CO_MI_EQUIPMENT_WORK_RECIPE WR			
		WHERE (WipOrderNo IS NOT NULL OR WipOrderNo != '')
		  AND WipOrderType IS NOT NULL
		  AND WR.Facility   = @Facility
		  AND WR.Equipment  = @Equipment
		  AND WR.SendStatus = 0;
	END

	RETURN
END