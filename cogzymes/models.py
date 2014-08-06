from django.db import models


class Organism(models.Model):
    """An organism."""
    
    taxonomy_id = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return "<Organism (Taxonomy ID: %s)>" % self.taxonomy_id


class Cog(models.Model):
    """ A Cluster of Orthologous Groups, including unsupervised COGs (NOGs)."""
    
    name = models.CharField(max_length=20, unique=True)
    
    def __unicode__(self):
        return "%s" % self.id


class Gene(models.Model):
    """A gene, with locus tag corresponding to NOG data file."""
    
    locus_tag = models.CharField(max_length=100)
    organism = models.ForeignKey(Organism)
    cogs = models.ManyToManyField(Cog)
    
    class Meta:
        unique_together = ('locus_tag','organism')
    
    def __unicode__(self):
        return "<Gene (locus tag: %s - %s)>" % (self.locus_tag, self.organism.taxonomy_id)


# class Reaction(models.Model):
#     """Reaction, as defined in MetaNetX."""
#     
#     mnx_id = models.CharField(max_length=250, unique=True)
#     name = models.CharField(max_length=2500)
#     
#     def __unicode__(self):
#         return "<Reaction (MNX ID: %s)>" % self.mnx_id

# class Reactionsynonymsource(models.Model):
#     """The set of source DBs that the synonyms come from."""
#     
#     name = models.CharField(max_length=20, primary_key = True)
# 
# class Reactionsynonym(models.Model):
#     """A set of synonyms from MNXRef for determining which reactions are which in various models."""
#     
#     synonym = models.CharField(max_length=1000)
#     source = models.ForeignKey(Reactionsynonymsource)
#     reaction = models.ForeignKey(Reaction)

# class Metabolicmodel(models.Model):
#     """A metabolic model imported from SBML."""
#     
#     
#     id = models.CharField(max_length=50, primary_key = True)
#     organism = models.ForeignKey(Organism)
#     reactions = models.ManyToManyField('annotation.Reaction', related_name='+')
#     
#     def __unicode__(self):
#         return "<Metabolic Model (ID: %s)>" % self.id
    

# class Modelrxn(models.Model):
#     """A specific reaction in a Metabolicmodel, including model-specific ID."""
#     
#     id = models.CharField(max_length=250, primary_key = True)
#     metabolicmodel = models.ForeignKey(Metabolicmodel)
#     reaction = models.ForeignKey(Reaction)
#     
#     def __unicode__(self):
#         return "<Model Reaction (ID: %s)>" % self.name
    

class Enzyme(models.Model):
    """Protein complex that catalyses metabolic reactions."""
     
    ## Name must be concatenated ordered list of gene names separated by commas
    name = models.CharField(max_length=2500)
    genes = models.ManyToManyField(Gene)
    source = models.ForeignKey('annotation.Source', related_name = 'cog_enzymes')
    reactions = models.ManyToManyField('annotation.Model_reaction', related_name = 'cog_enzymes')
    type = models.ForeignKey('Enzyme_type')
     
    def __unicode__(self):
        return "%s (%s for organism %s)" % (self.name, self.source.name, self.source.organism.taxonomy_id)


class Cogzyme(models.Model):
    """COG list representing metabolic enzyme."""
    
#     def __init__(self, cog_list):
#         name_list = (cog.id for cog in cog_list)
#         self.name
    
    name = models.CharField(max_length=255, unique = True)
    cogs = models.ManyToManyField(Cog)
    enzymes = models.ManyToManyField(Enzyme)
    
    def __unicode__(self):
        return "<Cogzyme (COGs: %s)>" % self.name


class Enzyme_type(models.Model):
    """What is the source of the Enzyme?  Direct from model?"""
    
    type = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=1000, default = '')
    
class Reaction_preds(models.Model):
    """What reactions are predicted to be present in a dev (development) organism 
    from a ref (reference) model?
    N.B. The dev model can be deduced from which reaction (Model_reaction) is predicted.
    """

    status_choices = (
        ('add','add'),
        ('rem','remove')
    )
        
    dev_organism = models.ForeignKey(Organism)
    reaction = models.ForeignKey('annotation.Model_reaction')
    
    status = models.CharField(max_length=3, choices=status_choices, default='add')
    
    num_enzymes = models.IntegerField()
    enzyme_type = models.ForeignKey(Enzyme_type)
   
    
    
    
    
    