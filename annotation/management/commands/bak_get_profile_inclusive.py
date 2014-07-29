# Get inclusive results for a list of COGs in a file

from django.core.management.base import NoArgsCommand, CommandError
from MODELS.models import *
import gapstats as GS
from operator import itemgetter
import sys, re, copy
from time import *

class Command(NoArgsCommand):
    
    help = 'Takes a COG and gets the inclusive page of results from MTG.'
        
    def handle(self, **options):
        
        #
        cog_id = 'COG0002'
        
        output = cog_rxn(cog_id, GAP_STATUS)
        
        inc_results = output["inclusive"]
	
	num_results = 0
	for result in inc_results:
	    if float(result['phgf']) < 1e-5:
		print result

GAP_STATUS = dict([("0","absent"),("1","annotated"),("I","gap"),("G","gap"),("B","gap"),("O","gap"),("R","absent"),("S","absent"),("U","gap"),("A","gap")])

def cog_rxn(COG, GAP_STATUS):
	COGName=cog_info.objects.filter(COG=COG).values_list("COGName",flat=True)[0].encode("ascii","ignore")
	profile = cog_info.objects.filter(COG=COG).values_list("COGPhyloProfile",flat=True)[0].encode('ascii','ignore')
	rxnAssigned=[]
	if unicode(COG) in list(cog_info.objects.values_list("COG",flat=True).distinct()):
		rxnAssigned=cog_info.objects.filter(COG=COG).values_list("Associatedrxn",flat=True)[0].encode('ascii','ignore')
		rxnAssigned=rxnAssigned.split(",")
	results = cog_rxn_searches(COG,COGName,profile, GAP_STATUS)
	return {
                "COGID": COG,
	 	"COGName": COGName,
            	"profile": cog_rxn_profile(COG,COGName,profile, GAP_STATUS),
		"rxns": rxnAssigned, 
		"inclusive": results["inclusive"]["ResultInfoLst"],
	   	"exclusive": results["exclusive"]["ResultInfoLst"]
		}

def cog_rxn_profile(COG,COGName,profile, GAP_STATUS):
	seed_list = [SEED.encode("ascii","ignore") for (SEED,Species) in organisms.objects.values_list("SEED","Species")]
	species = dict(organisms.objects.values_list("SEED","Species").distinct())
	status = {seed_list[i]:GAP_STATUS[profile[i]] for i in range(0,len(seed_list))}
	sequences = dict()
	ncbi = dict()
	for seed in seed_list:
		sequences[seed] = []
		ncbi_match = re.search(r"(\D+)(\d+)\.(\d+)",seed)
		ncbi[seed] = ncbi_match.group(2)
	eggnog_GIs = []
	eggnog_SEED = {}
	eggnog_Seq = {}
	for (GI,SEED,Seq) in eggnog.objects.filter(COG=unicode(COG)).values_list("GI","SEED","Seq"):
		eggnog_GIs.append(GI)
		eggnog_SEED[GI] = SEED
		eggnog_Seq[GI] = Seq

	rxnlinks2 = {}
	for s,r,e in known_rxncog_association.objects.filter(COG=COG).values_list("SEEDPeg","rxn","e"):
		exrxn,exe = rxnlinks2.setdefault(s,["",100])
		e = float(e)
		if e < exe and e < 1e-26:
			rxnlinks2[s] = [r,e] 

	rxnlinks1 = {x:(y,z) for x,y,z in peg_info.objects.filter(GI__in=eggnog_GIs).values_list("GI","SEEDPeg","rxn")}

	for GI in eggnog_GIs:
		SEED = eggnog_SEED[GI]
		Seq = eggnog_Seq[GI]
		d = list()
		if(sequences.has_key(SEED)):
			d = sequences[SEED]
		rxn = ""
		SEEDPeg = ""
		if(rxnlinks1.has_key(GI)):
			SEEDPeg,rxn = rxnlinks1[GI]
			if(rxn == "" and rxnlinks2.has_key(SEEDPeg)):
				rxn = rxnlinks2[SEEDPeg][0]
		d.append({"SEEDPeg":SEEDPeg,"GI":GI,"rxn":rxn,"Seq":Seq})
		sequences[SEED] = d

	rows = list({"seed":seed,"species":species[seed],"ncbi":ncbi[seed],"status":status[seed],"sequences":sequences[seed]} for seed in seed_list)
	return rows

def cog_rxn_searches(Q,COGName,COGPhyloProfile, GAP_STATUS):
	
	
	Masking_dict={	"inclusive":dict([("0","0"),("1","1"),("I","1"),("G","1"),("B","1"),("O","1"),("R","0"),("S","0"),("U","1"),("A","1")]),
		        "exclusive":dict([("0","0"),("1","0"),("I","1"),("G","1"),("B","1"),("O","1"),("R","0"),("S","0"),("U","1"),("A","1")])}
	
	#A list of all cogs in the DB
	COGAll=cog_info.objects.exclude(COGPhyloProfile=unicode("0"*len(organisms.objects.all()))).values_list("COG",flat=True).distinct()
	#A list of COGs already assigned (by SEED model) to the investigated rxn
	COGAssigned=[]
	if unicode(Q) in list(rxn_info.objects.values_list("rxn",flat=True).distinct()):
		COGAssigned=rxn_info.objects.filter(rxn=Q).values_list("AssignedCOG",flat=True)[0].encode('ascii','ignore')
		COGAssigned=COGAssigned.split(",")

	#A list of all "informative i.e. non empty phyloprofile" rxns in the DB
	rxnAll=list(set(rxn_info.objects.exclude(rxnPhyloProfileOriginal=unicode("0"*len(organisms.objects.all()))).values_list("rxn",flat=True).distinct()))
	
	#A list of rxns already associated (by SEED model) with the investigated COG
	rxnAssociated=cog_info.objects.filter(COG=Q).values_list("Associatedrxn",flat=True)[0].encode('ascii','ignore')
	rxnAssociated=rxnAssociated.split(",")

	#Dictionary for result presentation
	ResultShowDct={}


	MaskingLst=["inclusive","exclusive"]
	#wantted masking
	#if "MaskingCheck" in request.GET and request.GET.getlist(u'MaskingCheck'):
	#	MaskingLst=[MaskingCheck.encode("ascii","ignore") for MaskingCheck in request.GET.getlist(u'MaskingCheck')]

	
	rxnPhyloProfileOriginals=dict(rxn_info.objects.values_list("rxn","rxnPhyloProfileOriginal"))
	rxnNames=dict(rxn_info.objects.values_list("rxn","rxnName"))
	Assocs = {x:(y,z) for x,y,z in rxn_info.objects.values_list("rxn","AssignedCOG","AssignedCOGCount")}

	#For each masking...
	for Masking in MaskingLst:
		#For each rxn...
		for i in range(0,len(rxnAll)):
			#rxn profile in a list of int format...it contains either 1 or 0
			rxnPhyloProfileOriginal=rxnPhyloProfileOriginals[unicode(rxnAll[i])].encode('ascii','ignore')
			#Get the function/name of the current COG (30 letters)
			rxnName=rxnNames[unicode(rxnAll[i])].encode('ascii','ignore')
	
			rxnGapCount=sum([rxnPhyloProfileOriginal.count(GapType) for GapType in ["G","I","B","O","A","U"]])
			GapFilledCount=sum([1 for rxnFilling,COGStatus in zip(rxnPhyloProfileOriginal,COGPhyloProfile) if((rxnFilling in ["G","I","B","O","A","U"]) & (COGStatus=="1"))])

			MaskedrxnPhyloProfile="".join([Masking_dict[Masking][entry] for entry in rxnPhyloProfileOriginal])
			#Profile comparison
			if MaskedrxnPhyloProfile != "0"*len(organisms.objects.all()):
				ResultLst=GS.Profile_comparison(MaskedrxnPhyloProfile,COGPhyloProfile)+[
					("SubjectID",rxnAll[i].encode("ascii","ignore")),
					("SubjectName",rxnName),
					("rxnGapCount",rxnGapCount),
					("GapFilledCount",GapFilledCount),]

				#If the COG has been assigned to the reaction, marked with *
				if rxnAll[i] in rxnAssociated:
					(AssignedCOGLst,AssignedCOGCountLst) = Assocs[unicode(rxnAll[i])]
					rxnCount=AssignedCOGCountLst.split(",")[AssignedCOGLst.split(",").index(unicode(Q))].encode("ascii","ignore")
					ResultLst.append(("AssociationCount","*%s*"%rxnCount))
				else:
					ResultLst.append(("AssociationCount",""))
				#Put the result in the dictionary for result representation
				#dict(ResultLst)={"phgf":##,"a":##,"b":##,"c":##,"SubjectID":@@,"SubjectName":@@,"rxnGapCount":##,"GapFilledCount":##,"AssociationCount":###}
				ResultShowDct.setdefault(Masking,[]).append(dict(ResultLst))

						#########################
						#3 RESULT REPRESENTATION#
						#########################
								####################
								#sorting the result#
								####################
	for (Masking,ResultDctLst) in ResultShowDct.iteritems():
		ResultShowDct[Masking]=sorted(ResultDctLst, key=itemgetter("phgf"))
		Rank=0
		for ResultDct in ResultShowDct[Masking]:
			Rank+=1
			ResultDct["Rank"]=Rank
			ResultDct["phgf"]="%.2e"%min(ResultDct["phgf"]*len(ResultShowDct[Masking]),1)
		ResultShowDct[Masking]={
			"ResultInfoLst":ResultShowDct[Masking],
			"SubjectIDLst":["*"+ResultDct["SubjectID"]+"*" if ResultDct["AssociationCount"]!="" else ResultDct["SubjectID"] for ResultDct in ResultShowDct[Masking]]
			}
	return ResultShowDct
