# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Reaction_pred.dev_organism'
        db.delete_column(u'cogzymes_reaction_pred', 'dev_organism_id')

        # Deleting field 'Reaction_pred.ref_organism'
        db.delete_column(u'cogzymes_reaction_pred', 'ref_organism_id')

        # Adding field 'Reaction_pred.dev_model'
        db.add_column(u'cogzymes_reaction_pred', 'dev_model',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='dev_model_preds', to=orm['annotation.Source']),
                      keep_default=False)

        # Adding field 'Reaction_pred.ref_model'
        db.add_column(u'cogzymes_reaction_pred', 'ref_model',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='ref_model_preds', to=orm['annotation.Source']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Reaction_pred.dev_organism'
        db.add_column(u'cogzymes_reaction_pred', 'dev_organism',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='dev_organism_preds', to=orm['cogzymes.Organism']),
                      keep_default=False)

        # Adding field 'Reaction_pred.ref_organism'
        db.add_column(u'cogzymes_reaction_pred', 'ref_organism',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='ref_organism_preds', to=orm['cogzymes.Organism']),
                      keep_default=False)

        # Deleting field 'Reaction_pred.dev_model'
        db.delete_column(u'cogzymes_reaction_pred', 'dev_model_id')

        # Deleting field 'Reaction_pred.ref_model'
        db.delete_column(u'cogzymes_reaction_pred', 'ref_model_id')


    models = {
        u'annotation.catalyst': {
            'Meta': {'object_name': 'Catalyst'},
            'enzyme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Enzyme']"}),
            'evidence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Evidence']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
        },
        u'annotation.compartment': {
            'Meta': {'object_name': 'Compartment'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
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
        u'annotation.metabolite': {
            'Meta': {'object_name': 'Metabolite'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
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
        u'annotation.reaction': {
            'Meta': {'object_name': 'Reaction'},
            'balanced': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.source': {
            'Meta': {'object_name': 'Source'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['cogzymes.Organism']", 'null': 'True', 'blank': 'True'})
        },
        u'cogzymes.cog': {
            'Meta': {'object_name': 'Cog'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'cogzymes.cogzyme': {
            'Meta': {'object_name': 'Cogzyme'},
            'cogs': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Cog']", 'symmetrical': 'False'}),
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Enzyme']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'cogzymes.enzyme': {
            'Meta': {'object_name': 'Enzyme'},
            'genes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Gene']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'reactions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cog_enzymes'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cog_enzymes'", 'to': u"orm['annotation.Source']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cogzymes.Enzyme_type']"})
        },
        u'cogzymes.enzyme_type': {
            'Meta': {'object_name': 'Enzyme_type'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        u'cogzymes.gene': {
            'Meta': {'unique_together': "(('locus_tag', 'organism'),)", 'object_name': 'Gene'},
            'cogs': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Cog']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locus_tag': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cogzymes.Organism']"})
        },
        u'cogzymes.organism': {
            'Meta': {'object_name': 'Organism'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'taxonomy_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'cogzymes.reaction_pred': {
            'Meta': {'object_name': 'Reaction_pred'},
            'cogzyme': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['cogzymes.Cogzyme']", 'null': 'True', 'blank': 'True'}),
            'dev_model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dev_model_preds'", 'to': u"orm['annotation.Source']"}),
            'enzyme_type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['cogzymes.Enzyme_type']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_enzymes': ('django.db.models.fields.IntegerField', [], {}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Model_reaction']"}),
            'ref_model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ref_model_preds'", 'to': u"orm['annotation.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'add'", 'max_length': '3'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'unk'", 'max_length': '3'})
        }
    }

    complete_apps = ['cogzymes']