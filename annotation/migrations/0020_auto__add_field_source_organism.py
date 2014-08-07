# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Source.organism'
        db.add_column(u'annotation_source', 'organism',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['cogzymes.Organism'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Source.organism'
        db.delete_column(u'annotation_source', 'organism_id')


    models = {
        u'annotation.catalyst': {
            'Meta': {'object_name': 'Catalyst'},
            'enzyme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Enzyme']"}),
            'evidence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Evidence']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
        },
        u'annotation.catalyst_ec': {
            'Meta': {'object_name': 'Catalyst_ec'},
            'ec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.EC']"}),
            'enzyme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Enzyme']"}),
            'evidence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.NCBI']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'annotation.catalyst_go': {
            'Meta': {'object_name': 'Catalyst_go'},
            'enzyme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Enzyme']"}),
            'evidence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.FFPred']"}),
            'go_term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'annotation.cogzyme_prediction': {
            'Meta': {'object_name': 'Cogzyme_prediction'},
            'cog_field': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'gpr': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
        },
        u'annotation.combfunc_prediction': {
            'Meta': {'object_name': 'Combfunc_prediction'},
            'combfunc_score': ('django.db.models.fields.FloatField', [], {}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_predictions_gene': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_go': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_reaction': ('django.db.models.fields.IntegerField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Combfunc_result']"}),
            'total_score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.combfunc_result': {
            'Meta': {'object_name': 'Combfunc_result'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go_term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.compartment': {
            'Meta': {'object_name': 'Compartment'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.direction': {
            'Meta': {'object_name': 'Direction'},
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'annotation.ec': {
            'Meta': {'object_name': 'EC'},
            'enzymes_ec': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst_ec']", 'symmetrical': 'False'}),
            'go_terms': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['annotation.GO']", 'null': 'True', 'through': u"orm['annotation.GO2EC']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'reactions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Reaction']", 'through': u"orm['annotation.EC_Reaction']", 'symmetrical': 'False'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.ec_reaction': {
            'Meta': {'object_name': 'EC_Reaction'},
            'ec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.EC']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.eficaz_prediction': {
            'Meta': {'object_name': 'Eficaz_prediction'},
            'eficaz_score': ('django.db.models.fields.FloatField', [], {}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_predictions_ec': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_gene': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_reaction': ('django.db.models.fields.IntegerField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Eficaz_result']"}),
            'total_score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.eficaz_result': {
            'Meta': {'object_name': 'Eficaz_result'},
            'ec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.EC']"}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'precision_mean': ('django.db.models.fields.FloatField', [], {}),
            'precision_sd': ('django.db.models.fields.FloatField', [], {}),
            'seq_id_bin': ('django.db.models.fields.IntegerField', [], {})
        },
        u'annotation.enzyme': {
            'Meta': {'object_name': 'Enzyme'},
            'genes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Gene']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.evidence': {
            'Meta': {'object_name': 'Evidence'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.FloatField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.ffpred': {
            'Meta': {'object_name': 'FFPred'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.ffpred_prediction': {
            'Meta': {'object_name': 'FFPred_prediction'},
            'ffpred_score': ('django.db.models.fields.FloatField', [], {}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_predictions_gene': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_go': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_reaction': ('django.db.models.fields.IntegerField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'total_score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.ffpred_result': {
            'Meta': {'object_name': 'FFPred_result'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go_term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.gene': {
            'Meta': {'object_name': 'Gene'},
            'annotation': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'cog_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '7', 'null': 'True', 'blank': 'True'}),
            'gi': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'locus': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'locus_tag': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'protein_gi': ('django.db.models.fields.IntegerField', [], {})
        },
        u'annotation.go': {
            'Meta': {'object_name': 'GO'},
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst_go']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'annotation.go2ec': {
            'Meta': {'object_name': 'GO2EC'},
            'ec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.EC']"}),
            'go': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'annotation.go_reaction': {
            'Meta': {'object_name': 'GO_Reaction'},
            'ec': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.EC']"}),
            'go': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'annotation.iah991_prediction': {
            'Meta': {'object_name': 'Iah991_prediction'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_predictions_gene': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_reaction': ('django.db.models.fields.IntegerField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
        },
        u'annotation.metabolic_model': {
            'Meta': {'object_name': 'Metabolic_model'},
            'direction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Direction']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.metabolite': {
            'Meta': {'object_name': 'Metabolite'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.metabolite_synonym': {
            'Meta': {'object_name': 'Metabolite_synonym'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inferred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'metabolite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Metabolite']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'annotation.method': {
            'Meta': {'object_name': 'Method'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'annotation.model_metabolite': {
            'Meta': {'object_name': 'Model_metabolite'},
            'compartment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Compartment']"}),
            'curated_db_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'db_metabolite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Metabolite']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.model_reaction': {
            'Meta': {'object_name': 'Model_reaction'},
            'curated_db_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'db_reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']", 'null': 'True', 'blank': 'True'}),
            'gpr': ('django.db.models.fields.CharField', [], {'max_length': '10000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapping': ('django.db.models.fields.related.ManyToManyField', [], {'default': 'None', 'to': u"orm['annotation.Model_reaction_mapping']", 'through': u"orm['annotation.Model_reaction_to_mapping']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'metabolites': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'metabolites_related'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_metabolite']"}),
            'model_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'products_related'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_metabolite']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'substrates': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Model_metabolite']", 'symmetrical': 'False'})
        },
        u'annotation.model_reaction_mapping': {
            'Meta': {'object_name': 'Model_reaction_mapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'})
        },
        u'annotation.model_reaction_to_mapping': {
            'Meta': {'object_name': 'Model_reaction_to_mapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Method']"}),
            'model_reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Model_reaction']"}),
            'model_reaction_mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Model_reaction_mapping']"})
        },
        u'annotation.mtg_cog_result': {
            'Meta': {'object_name': 'MTG_cog_result'},
            'cog_id': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'p_value': ('django.db.models.fields.FloatField', [], {}),
            'rank': ('django.db.models.fields.IntegerField', [], {}),
            'seed_id': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'annotation.mtg_prediction': {
            'Meta': {'object_name': 'Mtg_prediction'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
        },
        u'annotation.ncbi': {
            'Meta': {'object_name': 'NCBI'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.profunc_prediction': {
            'Meta': {'object_name': 'Profunc_prediction'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_predictions_gene': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_go': ('django.db.models.fields.IntegerField', [], {}),
            'num_predictions_reaction': ('django.db.models.fields.IntegerField', [], {}),
            'profunc_score': ('django.db.models.fields.FloatField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'total_score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.profunc_prediction2': {
            'Meta': {'object_name': 'Profunc_prediction2'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Profunc_result']"}),
            'score': ('django.db.models.fields.FloatField', [], {}),
            'total_score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.profunc_result': {
            'Meta': {'object_name': 'Profunc_result'},
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Gene']"}),
            'go_term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.GO']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.FloatField', [], {})
        },
        u'annotation.reaction': {
            'Meta': {'object_name': 'Reaction'},
            'balanced': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.reaction_synonym': {
            'Meta': {'object_name': 'Reaction_synonym'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inferred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'annotation.source': {
            'Meta': {'object_name': 'Source'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['cogzymes.Organism']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.stoichiometry': {
            'Meta': {'object_name': 'Stoichiometry'},
            'compartment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Compartment']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metabolite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Metabolite']"}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'stoichiometry': ('django.db.models.fields.FloatField', [], {})
        },
        u'cogzymes.organism': {
            'Meta': {'object_name': 'Organism'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'taxonomy_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['annotation']