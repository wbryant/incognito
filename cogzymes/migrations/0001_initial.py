# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
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

        # Adding unique constraint on 'Gene', fields ['locus_tag', 'organism']
        db.create_unique(u'cogzymes_gene', ['locus_tag', 'organism_id'])

        # Adding M2M table for field cogs on 'Gene'
        m2m_table_name = db.shorten_name(u'cogzymes_gene_cogs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('gene', models.ForeignKey(orm[u'cogzymes.gene'], null=False)),
            ('cog', models.ForeignKey(orm[u'cogzymes.cog'], null=False))
        ))
        db.create_unique(m2m_table_name, ['gene_id', 'cog_id'])

        # Adding model 'Enzyme'
        db.create_table(u'cogzymes_enzyme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cog_enzymes', to=orm['annotation.Source'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cogzymes.Enzyme_type'])),
            ('new_cogzyme', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='cog_enzymes', null=True, blank=True, to=orm['cogzymes.Cogzyme'])),
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
            ('model_reaction', models.ForeignKey(orm[u'annotation.model_reaction'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'model_reaction_id'])

        # Adding model 'Cogzyme'
        db.create_table(u'cogzymes_cogzyme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
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

        # Adding model 'Enzyme_type'
        db.create_table(u'cogzymes_enzyme_type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=1000)),
        ))
        db.send_create_signal(u'cogzymes', ['Enzyme_type'])

        # Adding model 'Reaction_pred'
        db.create_table(u'cogzymes_reaction_pred', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Model_reaction'])),
            ('dev_model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dev_model_preds', to=orm['annotation.Source'])),
            ('ref_model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ref_model_preds', to=orm['annotation.Source'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='unk', max_length=3)),
            ('status', self.gf('django.db.models.fields.CharField')(default='add', max_length=3)),
            ('num_enzymes', self.gf('django.db.models.fields.IntegerField')()),
            ('enzyme_type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['cogzymes.Enzyme_type'], null=True, blank=True)),
            ('cogzyme', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['cogzymes.Cogzyme'], null=True, blank=True)),
        ))
        db.send_create_signal(u'cogzymes', ['Reaction_pred'])


    def backwards(self, orm):
        # Removing unique constraint on 'Gene', fields ['locus_tag', 'organism']
        db.delete_unique(u'cogzymes_gene', ['locus_tag', 'organism_id'])

        # Deleting model 'Organism'
        db.delete_table(u'cogzymes_organism')

        # Deleting model 'Cog'
        db.delete_table(u'cogzymes_cog')

        # Deleting model 'Gene'
        db.delete_table(u'cogzymes_gene')

        # Removing M2M table for field cogs on 'Gene'
        db.delete_table(db.shorten_name(u'cogzymes_gene_cogs'))

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

        # Deleting model 'Enzyme_type'
        db.delete_table(u'cogzymes_enzyme_type')

        # Deleting model 'Reaction_pred'
        db.delete_table(u'cogzymes_reaction_pred')


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
        u'annotation.mapping': {
            'Meta': {'object_name': 'Mapping'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction_group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Method']"}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reaction_mapped'", 'to': u"orm['annotation.Model_reaction']"})
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
            'db_mapping_method': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'db_reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']", 'null': 'True', 'blank': 'True'}),
            'gpr': ('django.db.models.fields.CharField', [], {'max_length': '10000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapping': ('django.db.models.fields.related.ManyToManyField', [], {'default': 'None', 'to': u"orm['annotation.Reaction_group']", 'through': u"orm['annotation.Mapping']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'metabolites': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'metabolites_of_reaction'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_metabolite']"}),
            'model_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'products_of_reaction'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_metabolite']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'substrates': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'substrates_of_reaction'", 'symmetrical': 'False', 'to': u"orm['annotation.Model_metabolite']"})
        },
        u'annotation.reaction': {
            'Meta': {'object_name': 'Reaction'},
            'balanced': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"})
        },
        u'annotation.reaction_group': {
            'Meta': {'object_name': 'Reaction_group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'})
        },
        u'annotation.source': {
            'Meta': {'object_name': 'Source'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['cogzymes.Organism']", 'null': 'True', 'blank': 'True'}),
            'reference_model': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
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
            'new_cogzyme': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'cog_enzymes'", 'null': 'True', 'blank': 'True', 'to': u"orm['cogzymes.Cogzyme']"}),
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