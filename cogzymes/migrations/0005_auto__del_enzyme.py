# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Enzyme'
        db.delete_table(u'cogzymes_enzyme')

        # Removing M2M table for field reactions on 'Enzyme'
        db.delete_table(db.shorten_name(u'cogzymes_enzyme_reactions'))

        # Removing M2M table for field genes on 'Enzyme'
        db.delete_table(db.shorten_name(u'cogzymes_enzyme_genes'))

        # Removing M2M table for field enzymes on 'Cogzyme'
        db.delete_table(db.shorten_name(u'cogzymes_cogzyme_enzymes'))


    def backwards(self, orm):
        # Adding model 'Enzyme'
        db.create_table(u'cogzymes_enzyme', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cog_enzymes', to=orm['annotation.Source'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'cogzymes', ['Enzyme'])

        # Adding M2M table for field reactions on 'Enzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_enzyme_reactions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False)),
            ('reaction', models.ForeignKey(orm[u'annotation.reaction'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'reaction_id'])

        # Adding M2M table for field genes on 'Enzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_enzyme_genes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False)),
            ('gene', models.ForeignKey(orm[u'cogzymes.gene'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'gene_id'])

        # Adding M2M table for field enzymes on 'Cogzyme'
        m2m_table_name = db.shorten_name(u'cogzymes_cogzyme_enzymes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cogzyme', models.ForeignKey(orm[u'cogzymes.cogzyme'], null=False)),
            ('enzyme', models.ForeignKey(orm[u'cogzymes.enzyme'], null=False))
        ))
        db.create_unique(m2m_table_name, ['cogzyme_id', 'enzyme_id'])


    models = {
        u'cogzymes.cog': {
            'Meta': {'object_name': 'Cog'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'cogzymes.cogzyme': {
            'Meta': {'object_name': 'Cogzyme'},
            'cogs': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cogzymes.Cog']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000'})
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