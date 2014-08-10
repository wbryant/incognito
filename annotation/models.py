from django.db import models
import sys

class Source(models.Model):
    """Source for all information in the DB - in development!"""
    
    name = models.CharField(max_length=50, primary_key = True)
    
    ## For metabolic models, state which organism the model is for
    organism = models.ForeignKey('cogzymes.Organism', blank=True, null=True, default=None)
    
    def __unicode__(self):
        return self.name
    
## Entities
class Gene(models.Model):
    """NCBI genes."""
    
    gi = models.IntegerField(primary_key = True)
    locus = models.CharField(max_length = 10)
    locus_tag = models.CharField(max_length = 10)
    name = models.CharField(max_length = 200)
    annotation = models.CharField(max_length = 200)
    cog_id = models.CharField(max_length=7, default=None, null=True, blank=True)
    
    protein_gi = models.IntegerField()

    def __unicode__(self):
        return self.locus_tag

class Enzyme(models.Model):
    """Protein complexes that catalyse metabolic reactions."""
    
    name = models.CharField(max_length=1000)
    genes = models.ManyToManyField(Gene)
    source = models.ForeignKey(Source)
    
    def __unicode__(self):
        return self.name


class Reaction(models.Model):
    """Metabolic reactions that can occur - using MNXref as cross-reference."""
    
    name = models.CharField(max_length=100)    
    source = models.ForeignKey(Source)
    enzymes = models.ManyToManyField(Enzyme, through='Catalyst')
    balanced = models.BooleanField(default=True)
    unique_together = ("name","source")
    
    def __unicode__(self):
        try:
            return "%s (%s)" % (self.name, self.source.name)
        except:
            return "%s (no source)" % (self.name)
    
    def metprint(self):
        """
        For comparison with model reactions, get two sets of db_metabolites, produced or consumed by this reaction.
        """

        ## Get metabolite details
        stos = self.stoichiometry_set.exclude(metabolite__id='MNXM1').prefetch_related('metabolite')
    
        subs_list = []
        prod_list = []
        complete = True
        
        for sto in stos:
            if sto.stoichiometry < 0:
                subs_list.append(sto.metabolite.id)
            elif sto.stoichiometry > 0:
                prod_list.append(sto.metabolite.id)
            else:
                complete = False
        
        subs_fset = frozenset(subs_list)
        prod_fset = frozenset(prod_list)
               
        return subs_fset, prod_fset, complete
        
    def equation(self):
        """
        Return a string representing the full stoichiometry of the reaction.
        """
        stos = self.stoichiometry_set.all()
    
        subs_list = []
        prods_list = []
        unknowns_list = []
        
        for sto in stos:
            if sto.stoichiometry < 0:
                subs_list.append(sto)
            elif sto.stoichiometry > 0:
                prods_list.append(sto)
            else:
                unknowns_list.append(sto)
        
        sub_string = ""
        
        for sub in subs_list:
            try:
                compartment = sub.compartment.id
            except:
                compartment = "unk"
            sub_string = sub_string + " + %1d %s[%s]" % (sub.stoichiometry*-1, sub.metabolite.name, compartment)
        sub_string = sub_string[3:]
        
        prod_string = ""
        
        for prod in prods_list:
            try:
                compartment = prod.compartment.id
            except:
                compartment = "unk"
            prod_string = prod_string + " + %1d %s[%s]" % (prod.stoichiometry, prod.metabolite.name, compartment)
        prod_string = prod_string[3:]
        
        unknown_string = ""
        
        for unknown in unknowns_list:
            try:
                compartment = unknown.compartment.id
            except:
                compartment = "unk"
            unknown_string = unknown_string + " + (unk) %s[%s]" % (unknown.metabolite.name, compartment)
        unknown_string = unknown_string[3:]
        
        equation = sub_string + " ==> " + prod_string 
        
        if len(unknown_string) > 0:
            equation = equation + " (%s)" % unknown_string
        
        return equation
    
    def met_model_connection(self, mm_source_id):
        """
        Return the number of metabolites from this reaction already in a metabolic model.
        """
        
        try:
            source = Source.objects.get(name=mm_source_id)
        except:
            print("Source could not be identified ...")
            sys.exit(1)
        
        mm_mets = Metabolite.objects\
                    .filter(stoichiometry__reaction__metabolic_model__source=source)\
                    .distinct()\
                    .values_list("name", flat=True)
        
        rxn_mets = Metabolite.objects\
                    .filter(stoichiometry__reaction=self)\
                    .distinct()\
                    .values_list("name", flat=True)
        
        num_mets = rxn_mets.count()
        
        num_connected = 0
        
        for met in rxn_mets:
            if met in mm_mets:
                num_connected += 1
        
        print("Number of metabolites = %d" % num_mets)
        print("Number overlapping = %d" % num_connected)
        
        
        
class Reaction_synonym(models.Model):
    "Synonyms for reactions in MetaNetX"
    
    synonym = models.CharField(max_length=1000)
    inferred = models.BooleanField(default=False)
    reaction = models.ForeignKey(Reaction)
    
    source = models.ForeignKey(Source)

class GO(models.Model):
    #GO terms in molecular function
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=1000)
    
    enzymes = models.ManyToManyField(Enzyme, through='Catalyst_go')
    
    def __unicode__(self):
        return self.name + "(" + self.id + ")"

class EC(models.Model):
    # EC numbers and their m-to-m links to reactions and enzymes and links to GO terms where known
    
    number = models.CharField(max_length=20, primary_key = True)
    name = models.CharField(max_length = 1000)
    source = models.ForeignKey(Source, null=True, blank=True)
    
    go_terms = models.ManyToManyField(GO, blank = True, null = True, through='GO2EC')
    enzymes_ec = models.ManyToManyField(Enzyme, through='Catalyst_ec')
    reactions = models.ManyToManyField(Reaction, through='EC_Reaction')

    def __unicode__(self):
        return self.number

    #def __init__(self, sources):
    #    self.sources = sources


## Sources.  For several relationships there must be associated evidence from an analytical source or an existing metabolic model.  For each source there is a model and a foreign key in the relevant relationship.

class Evidence(models.Model):
    """What evidence is there for each catalyst/reaction pair?  Score normalised to -1 to 1."""
    score = models.FloatField()
    source = models.ForeignKey(Source, null=True, blank=True)
    
    #def __init__(self, sources):
    #    self.sources = sources


class FFPred(models.Model):
    """Table of GO predictions for all genes in BTH."""
    score = models.FloatField()
    #go_term = models.ForeignKey(GO)
    reliability = models.CharField(max_length=2)
    #domain = models.CharField(max_length=2)
    #description = models.CharField(max_length=200)
    
#class iAH991(models.Model):
#    """Table of enzyme/reaction associations in iAH991."""
#    
#    function = models.CharField(max_length=1000)
#    inference = models.ForeignKey(Evidence)
    
    
class NCBI(models.Model):
    """Table of gene(enzyme)/EC number associations."""
    
    score = models.FloatField()


## Relationships

class Catalyst(models.Model):
    """Which enzymes catalyse which reactions, and which piece of evidence supports it."""
    
    enzyme = models.ForeignKey(Enzyme)
    reaction = models.ForeignKey(Reaction)
    
    evidence = models.ForeignKey(Evidence)

class Catalyst_ec(models.Model):
    """Which enzymes catalyse which EC numbers, and which piece of evidence supports it."""
    
    enzyme = models.ForeignKey(Enzyme)
    ec = models.ForeignKey(EC)
    
    evidence = models.ForeignKey(NCBI)

class Catalyst_go(models.Model):
    """Which enzymes catalyse which GO terms, and which piece of evidence supports it."""
    
    enzyme = models.ForeignKey(Enzyme)
    go_term = models.ForeignKey(GO)
    
    evidence = models.ForeignKey(FFPred) 
    

# Inferred tables

class EC_Reaction(models.Model):
    """Many-to-many table for EC and Reaction."""
    
    ec = models.ForeignKey(EC)
    reaction = models.ForeignKey(Reaction)
    
    source = models.ForeignKey(Source, null=True, blank=True)

class GO_Reaction(models.Model):
    """Which GO terms refer to which specific reactions?"""
    
    go = models.ForeignKey(GO)
    ec = models.ForeignKey(EC)
    reaction = models.ForeignKey(Reaction)
    
    source = models.CharField(max_length=50)

class GO2EC(models.Model):
    """Which EC numbers are associated with which GO terms."""
    
    go = models.ForeignKey(GO)
    ec = models.ForeignKey(EC)
    source = models.CharField(max_length=50)


# Results tables - tables of results from other analyses, so that different integration techniques can be used.

class MTG_cog_result(models.Model):
    """Results from the Mind The Gap website for COGs present in the organism."""
    
    TYPE_CHOICES = (
        ('i', 'inclusive'),
        ('e', 'exclusive'),
    )
    
    cog_id = models.CharField(max_length=8) # COG ID
    seed_id = models.CharField(max_length=8) # SEED reaction ID
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    p_value = models.FloatField()
    rank = models.IntegerField()
    
class FFPred_result(models.Model):
    """Results from FFPred runs for each applicable gene."""
    
    gene = models.ForeignKey(Gene)
    go_term = models.ForeignKey(GO)
    score = models.FloatField()
    reliability = models.CharField(max_length=5)
    
class FFPred_prediction(models.Model):
    """Predictions of gene/reaction relationships from FFPred."""
    
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    go = models.ForeignKey(GO)
    
    ffpred_score = models.FloatField()
    num_predictions_go = models.IntegerField()
    num_predictions_gene = models.IntegerField()
    num_predictions_reaction = models.IntegerField()
    
    total_score = models.FloatField()

class Profunc_result(models.Model):
    """Results from Profunc runs for each applicable gene."""
    
    gene = models.ForeignKey(Gene)
    go_term = models.ForeignKey(GO)
    score = models.FloatField()
    
    
class Profunc_prediction(models.Model):
    """Predictions of gene/reaction relationships from Profunc."""
    
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    go = models.ForeignKey(GO)
    
    profunc_score = models.FloatField()
    num_predictions_go = models.IntegerField()
    num_predictions_gene = models.IntegerField()
    num_predictions_reaction = models.IntegerField()
    
    total_score = models.FloatField()

class Profunc_prediction2(models.Model):
    """Slim version of predictions for Profunc."""
    
    result = models.ForeignKey(Profunc_result)
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    
    score = models.FloatField()
    total_score = models.FloatField()

    
class Eficaz_result(models.Model):
    """Results from EFICAz 2.5 runs for each applicable gene."""
    
    gene = models.ForeignKey(Gene)
    ec = models.ForeignKey(EC)
    precision_mean = models.FloatField()
    precision_sd = models.FloatField()
    seq_id_bin = models.IntegerField()
    
class Eficaz_prediction(models.Model):
    """Predictions of gene/reaction relationships from EFICAz 2.5."""
    
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    result = models.ForeignKey(Eficaz_result)
    
    eficaz_score = models.FloatField()
    num_predictions_ec = models.IntegerField()
    num_predictions_gene = models.IntegerField()
    num_predictions_reaction = models.IntegerField()
    
    total_score = models.FloatField()
    
    def __unicode__(self):
        return "%s => %s (%.3f)" % (self.gene.locus_tag, self.reaction.name, self.total_score)


class Combfunc_result(models.Model):
    """Results from Combfunc runs for each applicable gene."""
    
    gene = models.ForeignKey(Gene)
    go_term = models.ForeignKey(GO)
    score = models.FloatField()
    
    
class Combfunc_prediction(models.Model):
    """Predictions of gene/reaction relationships from Combfunc."""
    
    result = models.ForeignKey(Combfunc_result)
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    go = models.ForeignKey(GO)
    
    combfunc_score = models.FloatField()
    num_predictions_go = models.IntegerField()
    num_predictions_gene = models.IntegerField()
    num_predictions_reaction = models.IntegerField()
    
    total_score = models.FloatField()

 
class Iah991_prediction(models.Model):
    """GPR relationships in iAH991 split into gene/reaction predictions for comparison."""
    
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)
    
    num_predictions_gene = models.IntegerField()
    num_predictions_reaction = models.IntegerField()
    
class Mtg_prediction(models.Model):
    """Gene predictions from Mind The Gap."""
    
    gene = models.ForeignKey(Gene)
    reaction = models.ForeignKey(Reaction)

class Cogzyme_prediction(models.Model):
    """Reaction predictions from E. coli model."""
    
    gpr = models.CharField(max_length=1000)
    cog_field = models.CharField(max_length=1000)
    reaction = models.ForeignKey(Reaction)

    
    
   
    
### Metabolite details

# class Metabolite_source(models.Model):
#     """All sources for metabolites."""
#     
#     name = models.CharField(max_length=50)
#     
#     def __unicode__(self):
#         return self.name

class Metabolite(models.Model):
    """Metabolites to be related to reactions, mainly from MNXRef."""
    
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=1000)
    source = models.ForeignKey(Source)
    
    def __unicode__(self):
        return self.id

# class Metabolite_synonym_source(models.Model):
#     """All sources for metabolite synonyms."""
#     
#     name = models.CharField(max_length=50)

class Metabolite_synonym(models.Model):
    """Synonyms for metabolites from MNXRef."""
    
    synonym = models.CharField(max_length=1000)
    inferred = models.BooleanField(default=False)
    metabolite = models.ForeignKey(Metabolite)
    source = models.ForeignKey(Source)
    
    def __unicode__(self):
        return "%s: %s (%s)" % (self.synonym, self.metabolite.id, self.source.name)

class Compartment(models.Model):
    """Metabolic compartments for all participants of each reaction."""
    
    id = models.CharField(max_length = 10, primary_key=True)
    name = models.CharField(max_length = 50)
    source = models.ForeignKey(Source, null=True, blank=True)
    
    def __unicode__(self):
        return "%s (ID: %s)" % (self.name, self.id)

class Direction(models.Model):
    """A table defining the directionalities that reactions can take in DB."""
    
    direction = models.CharField(max_length = 15)
    
    def __unicode__(self):
        return self.direction 

class Stoichiometry(models.Model):
    """Complete stoichiometry for reactions, from MetaNetX and others."""
    
    reaction = models.ForeignKey(Reaction)
    metabolite = models.ForeignKey(Metabolite)
    source = models.ForeignKey(Source)
    compartment = models.ForeignKey(Compartment, blank=True, null=True)
    #direction = models.ForeignKey(Direction, blank=True, null=True)
    
    ## Stoichiometry - negative for substrate, positive for product
    stoichiometry = models.FloatField()
    
    unique_together = ('reaction','metabolite','stoichiometry')
    
    def __unicode__(self):
        return "%s: %.1f %s" % (self.reaction, self.stoichiometry, self.metabolite.id)
    
class Metabolic_model(models.Model):
    """Reaction complements for metabolic model, with directionality."""
    
    source = models.ForeignKey(Source)
    reaction = models.ForeignKey(Reaction)
    direction = models.ForeignKey(Direction)
    

### Tables for storing developing model

class Model_metabolite(models.Model):
    """Metabolite present in the model being developed.
       - Includes compartment.
       - Includes link to DB metabolite."""
    
    model_id = models.CharField(max_length = 100)
    name = models.CharField(max_length = 1000)
    compartment = models.ForeignKey(Compartment)
    db_metabolite = models.ForeignKey(Metabolite, blank=True, null=True)
    source = models.ForeignKey(Source)
    curated_db_link = models.BooleanField(default=True)

    def __unicode__(self):
        return "{}".format(self.model_id)

class Model_reaction(models.Model):
    """Reaction present in the model being developed.
       - Includes source for reaction (original model/prediction source).
       - Includes link to DB reaction where possible.
       - Includes plain text GPR for reaction - to get prediction GPRs.
       - Includes links to all metabolites involved but without more information (for quick comparison).
       
       N.B. If there are multiple predictions of the same reaction, GPRs should be combined on export.
       
       MODEL REACTION:  This table should contain all reactions that are to be exported from the database,
       i.e. original model reactions (to ensure no duplicates in the predictions) and all predicted 
       reactions.  This table will then be used to export the model to SBML, through a management command.
       """
    
    model_id = models.CharField(max_length = 100)
    name = models.CharField(max_length = 2000)
    db_reaction = models.ForeignKey(Reaction, blank=True, null=True)
    source = models.ForeignKey(Source)
    gpr = models.CharField(max_length = 10000)
    substrates = models.ManyToManyField(Model_metabolite)
    products = models.ManyToManyField(Model_metabolite, related_name = 'products_related')
    metabolites = models.ManyToManyField(Model_metabolite, related_name = 'metabolites_related')
    curated_db_link = models.BooleanField(default=True)
    mapping = models.ManyToManyField('Reaction_group', blank=True, null=True, default=None, 
                                     through='Mapping')
    
    def __unicode__(self):
        return "{:10} ({})".format(self.model_id, self.name)

    def metprint(self):
        """
        For comparison with DB reactions, get two sets of db_metabolites, if available, produced or consumed by this reaction.
        """

        ## Get metabolite details
        
        subs_list = []
        prod_list = []
        complete = True
        
        for model_met in self.substrates.all():
            if model_met.db_metabolite:
                if model_met.db_metabolite.id != "MNXM1":
                    subs_list.append(model_met.db_metabolite.id)
            else:
                complete = False
                
        for model_met in self.products.all():
            if model_met.db_metabolite:
                if model_met.db_metabolite.id != "MNXM1":
                    prod_list.append(model_met.db_metabolite.id)
            else:
                complete = False
        
        subs_fset = frozenset(subs_list)
        prod_fset = frozenset(prod_list)
               
        return subs_fset, prod_fset, complete


## Mappings between SBML Models inferred by other means than through MNX
class Method(models.Model):
    """
    The method by which a mapping was inferred.
    """
    
    name = models.CharField(max_length=100)

class Reaction_group(models.Model):
    """
    A group of mapped reactions, linked to a reaction from at least 2 models from Model_reaction.
    
    This should be used in the case where reactions cannot be mapped to MNX reactions.
    """
    
    name = models.CharField(max_length=100,default='')
    
    def __unicode__(self):
        return self.name

class Mapping(models.Model):
    """through table noting the method used to map the reactions to the group 
    
    """
    
    group = models.ForeignKey(Reaction_group)
    reaction = models.ForeignKey(Model_reaction, 
                                 related_name = 'reaction_mapped')
    method = models.ForeignKey(Method)
    
    def __unicode__(self):
        return "Reaction {} ({}) -> Group '{}' ({} method)".format(
                                                self.reaction.model_id,
                                                self.reaction.source.name,
                                                self.group.name,
                                                self.method.name
                                                )