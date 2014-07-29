#! /bin/bash

#Repopulate the entire database using the latest imports!

./manage.py import_data_go          # GO
./manage.py import_data_reactions   # Reaction, EC, EC_Reaction
./manage.py import_data_ecgo        # EC, GO2EC
./manage.py import_data_genes       # Gene
./manage.py import_data_iAH991      # Evidence, Enzyme, Catalyst(, Reaction, EC, EC_Reaction)
./manage.py import_cog_profile      # MTG_cog_result
./manage.py import_data_ffpred      # FFPred_result
#./manage.py infer_go2ec             # GO2EC
./manage.py infer_go2reaction       # GO_Reaction
./manage.py analyse_ffpred          # FFPred_prediction