# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'Gene', fields ['locus_tag', 'organism']
        db.create_unique(u'cogzymes_gene', ['locus_tag', 'organism_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Gene', fields ['locus_tag', 'organism']
        db.delete_unique(u'cogzymes_gene', ['locus_tag', 'organism_id'])


    models = {
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'cogzymes.enzyme': {
            'Meta': {'object_name': 'Enzyme'},
            'genes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Gene']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metabolicmodel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cogzymes.Metabolicmodel']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'reactions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'enzymes'", 'symmetrical': 'False', 'to': u"orm['cogzymes.Reaction']"})
        },
        u'cogzymes.gene': {
            'Meta': {'unique_together': "(('locus_tag', 'organism'),)", 'object_name': 'Gene'},
            'cogs': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Cog']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locus_tag': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cogzymes.Organism']"})
        },
        u'cogzymes.metabolicmodel': {
            'Meta': {'object_name': 'Metabolicmodel'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cogzymes.Organism']"}),
            'reactions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'+'", 'symmetrical': 'False', 'to': u"orm['cogzymes.Reaction']"})
        },
        u'cogzymes.organism': {
            'Meta': {'object_name': 'Organism'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'taxonomy_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'cogzymes.reaction': {
            'Meta': {'object_name': 'Reaction'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mnx_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500'})
        }
    }

    complete_apps = ['cogzymes']