# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Metabolicmodel'
        db.delete_table(u'cogzymes_metabolicmodel')

        # Removing M2M table for field reactions on 'Metabolicmodel'
        db.delete_table(db.shorten_name(u'cogzymes_metabolicmodel_reactions'))

        # Deleting model 'Reaction'
        db.delete_table(u'cogzymes_reaction')

        # Deleting field 'Enzyme.metabolicmodel'
        db.delete_column(u'cogzymes_enzyme', 'metabolicmodel_id')

        # Adding field 'Enzyme.source'
        db.add_column(u'cogzymes_enzyme', 'source',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='cog_enzymes', to=orm['annotation.Source']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'Metabolicmodel'
        db.create_table(u'cogzymes_metabolicmodel', (
            ('organism', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cogzymes.Organism'])),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
        ))
        db.send_create_signal(u'cogzymes', ['Metabolicmodel'])

        # Adding M2M table for field reactions on 'Metabolicmodel'
        m2m_table_name = db.shorten_name(u'cogzymes_metabolicmodel_reactions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('metabolicmodel', models.ForeignKey(orm[u'cogzymes.metabolicmodel'], null=False)),
            ('reaction', models.ForeignKey(orm[u'cogzymes.reaction'], null=False))
        ))
        db.create_unique(m2m_table_name, ['metabolicmodel_id', 'reaction_id'])

        # Adding model 'Reaction'
        db.create_table(u'cogzymes_reaction', (
            ('mnx_id', self.gf('django.db.models.fields.CharField')(max_length=250, unique=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500)),
        ))
        db.send_create_signal(u'cogzymes', ['Reaction'])

        # Adding field 'Enzyme.metabolicmodel'
        db.add_column(u'cogzymes_enzyme', 'metabolicmodel',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['cogzymes.Metabolicmodel']),
                      keep_default=False)

        # Deleting field 'Enzyme.source'
        db.delete_column(u'cogzymes_enzyme', 'source_id')


    models = {
        u'annotation.catalyst': {
            'Meta': {'object_name': 'Catalyst'},
            'enzyme': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Enzyme']"}),
            'evidence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Evidence']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'cogzymes.enzyme': {
            'Meta': {'object_name': 'Enzyme'},
            'genes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Gene']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'reactions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cog_enzymes'", 'symmetrical': 'False', 'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cog_enzymes'", 'to': u"orm['annotation.Source']"})
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
        }
    }

    complete_apps = ['cogzymes']