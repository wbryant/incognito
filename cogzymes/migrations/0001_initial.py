# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Organism'
        db.create_table(u'cogzymes_organism', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('taxonomy_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal(u'cogzymes', ['Organism'])

        # Adding model 'Cog'
        db.create_table(u'cogzymes_cog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
        ))
        db.send_create_signal(u'cogzymes', ['Cog'])

        # Adding model 'Gene'
        db.create_table(u'cogzymes_gene', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('locus_tag', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('organism', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cogzymes.Organism'])),
        ))
        db.send_create_signal(u'cogzymes', ['Gene'])

        # Adding M2M table for field cogs on 'Gene'
        m2m_table_name = db.shorten_name(u'cogzymes_gene_cogs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('gene', models.ForeignKey(orm[u'cogzymes.gene'], null=False)),
            ('cog', models.ForeignKey(orm[u'cogzymes.cog'], null=False))
        ))
        db.create_unique(m2m_table_name, ['gene_id', 'cog_id'])

        # Adding model 'Reaction'
        db.create_table(u'cogzymes_reaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mnx_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=250)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500)),
        ))
        db.send_create_signal(u'cogzymes', ['Reaction'])

        # Adding model 'Metabolicmodel'
        db.create_table(u'cogzymes_metabolicmodel', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('organism', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cogzymes.Organism'])),
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

        # Adding model 'Enzyme'
        db.create_table(u'cogzymes_enzyme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('metabolicmodel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cogzymes.Metabolicmodel'])),
        ))
        db.send_create_signal(u'cogzymes', ['Enzyme'])

        # Adding M2M table for field genes on 'Enzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_enzyme_genes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False)),
            ('gene', models.ForeignKey(orm[u'cogzymes.gene'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'gene_id'])

        # Adding M2M table for field reactions on 'Enzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_enzyme_reactions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False)),
            ('reaction', models.ForeignKey(orm[u'cogzymes.reaction'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'reaction_id'])

        # Adding model 'Cogzyme'
        db.create_table(u'cogzymes_cogzyme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'cogzymes', ['Cogzyme'])

        # Adding M2M table for field cogs on 'Cogzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_cogzyme_cogs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cogzyme', models.ForeignKey(orm[u'cogzymes.cogzyme'], null=False)),
            ('cog', models.ForeignKey(orm[u'cogzymes.cog'], null=False))
        ))
        db.create_unique(m2m_table_name, ['cogzyme_id', 'cog_id'])

        # Adding M2M table for field enzymes on 'Cogzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_cogzyme_enzymes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cogzyme', models.ForeignKey(orm[u'cogzymes.cogzyme'], null=False)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False))
        ))
        db.create_unique(m2m_table_name, ['cogzyme_id', 'enzyme_id'])


    def backwards(self, orm):
        # Deleting model 'Organism'
        db.delete_table(u'cogzymes_organism')

        # Deleting model 'Cog'
        db.delete_table(u'cogzymes_cog')

        # Deleting model 'Gene'
        db.delete_table(u'cogzymes_gene')

        # Removing M2M table for field cogs on 'Gene'
        db.delete_table(db.shorten_name(u'cogzymes_gene_cogs'))

        # Deleting model 'Reaction'
        db.delete_table(u'cogzymes_reaction')

        # Deleting model 'Metabolicmodel'
        db.delete_table(u'cogzymes_metabolicmodel')

        # Removing M2M table for field reactions on 'Metabolicmodel'
        db.delete_table(db.shorten_name(u'cogzymes_metabolicmodel_reactions'))

        # Deleting model 'Enzyme'
        db.delete_table(u'cogzymes_enzyme')

        # Removing M2M table for field genes on 'Enzyme'
        db.delete_table(db.shorten_name(u'cogzymes_enzyme_genes'))

        # Removing M2M table for field reactions on 'Enzyme'
        db.delete_table(db.shorten_name(u'cogzymes_enzyme_reactions'))

        # Deleting model 'Cogzyme'
        db.delete_table(u'cogzymes_cogzyme')

        # Removing M2M table for field cogs on 'Cogzyme'
        db.delete_table(db.shorten_name(u'cogzymes_cogzyme_cogs'))

        # Removing M2M table for field enzymes on 'Cogzyme'
        db.delete_table(db.shorten_name(u'cogzymes_cogzyme_enzymes'))


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
            'Meta': {'object_name': 'Gene'},
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