# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Source'
        db.create_table(u'annotation_source', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
        ))
        db.send_create_signal(u'annotation', ['Source'])

        # Adding model 'Gene'
        db.create_table(u'annotation_gene', (
            ('gi', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('locus', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('locus_tag', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('annotation', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('cog_id', self.gf('django.db.models.fields.CharField')(default=None, max_length=7, null=True, blank=True)),
            ('protein_gi', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'annotation', ['Gene'])

        # Adding model 'Enzyme'
        db.create_table(u'annotation_enzyme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
        ))
        db.send_create_signal(u'annotation', ['Enzyme'])

        # Adding M2M table for field genes on 'Enzyme'
        m2m_table_name = db.shorten_name(u'annotation_enzyme_genes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('enzyme', models.ForeignKey(orm[u'annotation.enzyme'], null=False)),
            ('gene', models.ForeignKey(orm[u'annotation.gene'], null=False))
        ))
        db.create_unique(m2m_table_name, ['enzyme_id', 'gene_id'])

        # Adding model 'Reaction'
        db.create_table(u'annotation_reaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'], null=True, blank=True)),
        ))
        db.send_create_signal(u'annotation', ['Reaction'])

        # Adding model 'Reaction_synonym'
        db.create_table(u'annotation_reaction_synonym', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('synonym', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
        ))
        db.send_create_signal(u'annotation', ['Reaction_synonym'])

        # Adding model 'GO'
        db.create_table(u'annotation_go', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=10, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'annotation', ['GO'])

        # Adding model 'EC'
        db.create_table(u'annotation_ec', (
            ('number', self.gf('django.db.models.fields.CharField')(max_length=20, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'], null=True, blank=True)),
        ))
        db.send_create_signal(u'annotation', ['EC'])

        # Adding model 'Evidence'
        db.create_table(u'annotation_evidence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'], null=True, blank=True)),
        ))
        db.send_create_signal(u'annotation', ['Evidence'])

        # Adding model 'FFPred'
        db.create_table(u'annotation_ffpred', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal(u'annotation', ['FFPred'])

        # Adding model 'NCBI'
        db.create_table(u'annotation_ncbi', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['NCBI'])

        # Adding model 'Catalyst'
        db.create_table(u'annotation_catalyst', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enzyme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Enzyme'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('evidence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Evidence'])),
        ))
        db.send_create_signal(u'annotation', ['Catalyst'])

        # Adding model 'Catalyst_ec'
        db.create_table(u'annotation_catalyst_ec', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enzyme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Enzyme'])),
            ('ec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.EC'])),
            ('evidence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.NCBI'])),
        ))
        db.send_create_signal(u'annotation', ['Catalyst_ec'])

        # Adding model 'Catalyst_go'
        db.create_table(u'annotation_catalyst_go', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enzyme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Enzyme'])),
            ('go_term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('evidence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.FFPred'])),
        ))
        db.send_create_signal(u'annotation', ['Catalyst_go'])

        # Adding model 'EC_Reaction'
        db.create_table(u'annotation_ec_reaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.EC'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'], null=True, blank=True)),
        ))
        db.send_create_signal(u'annotation', ['EC_Reaction'])

        # Adding model 'GO_Reaction'
        db.create_table(u'annotation_go_reaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('go', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('ec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.EC'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'annotation', ['GO_Reaction'])

        # Adding model 'GO2EC'
        db.create_table(u'annotation_go2ec', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('go', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('ec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.EC'])),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'annotation', ['GO2EC'])

        # Adding model 'MTG_cog_result'
        db.create_table(u'annotation_mtg_cog_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cog_id', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('seed_id', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('p_value', self.gf('django.db.models.fields.FloatField')()),
            ('rank', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'annotation', ['MTG_cog_result'])

        # Adding model 'FFPred_result'
        db.create_table(u'annotation_ffpred_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('go_term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal(u'annotation', ['FFPred_result'])

        # Adding model 'FFPred_prediction'
        db.create_table(u'annotation_ffpred_prediction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('go', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('ffpred_score', self.gf('django.db.models.fields.FloatField')()),
            ('num_predictions_go', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_gene', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_reaction', self.gf('django.db.models.fields.IntegerField')()),
            ('total_score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['FFPred_prediction'])

        # Adding model 'Profunc_result'
        db.create_table(u'annotation_profunc_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('go_term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['Profunc_result'])

        # Adding model 'Profunc_prediction'
        db.create_table(u'annotation_profunc_prediction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('go', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.GO'])),
            ('profunc_score', self.gf('django.db.models.fields.FloatField')()),
            ('num_predictions_go', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_gene', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_reaction', self.gf('django.db.models.fields.IntegerField')()),
            ('total_score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['Profunc_prediction'])

        # Adding model 'Profunc_prediction2'
        db.create_table(u'annotation_profunc_prediction2', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Profunc_result'])),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('total_score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['Profunc_prediction2'])

        # Adding model 'Eficaz_result'
        db.create_table(u'annotation_eficaz_result', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('ec', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.EC'])),
            ('precision_mean', self.gf('django.db.models.fields.FloatField')()),
            ('precision_sd', self.gf('django.db.models.fields.FloatField')()),
            ('seq_id_bin', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'annotation', ['Eficaz_result'])

        # Adding model 'Eficaz_prediction'
        db.create_table(u'annotation_eficaz_prediction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Eficaz_result'])),
            ('eficaz_score', self.gf('django.db.models.fields.FloatField')()),
            ('num_predictions_ec', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_gene', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_reaction', self.gf('django.db.models.fields.IntegerField')()),
            ('total_score', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['Eficaz_prediction'])

        # Adding model 'Iah991_prediction'
        db.create_table(u'annotation_iah991_prediction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Gene'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('num_predictions_gene', self.gf('django.db.models.fields.IntegerField')()),
            ('num_predictions_reaction', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'annotation', ['Iah991_prediction'])

        # Adding model 'Metabolite'
        db.create_table(u'annotation_metabolite', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=100, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
        ))
        db.send_create_signal(u'annotation', ['Metabolite'])

        # Adding model 'Metabolite_synonym'
        db.create_table(u'annotation_metabolite_synonym', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('synonym', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('metabolite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Metabolite'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
        ))
        db.send_create_signal(u'annotation', ['Metabolite_synonym'])

        # Adding model 'Compartment'
        db.create_table(u'annotation_compartment', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=10, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'], null=True, blank=True)),
        ))
        db.send_create_signal(u'annotation', ['Compartment'])

        # Adding model 'Direction'
        db.create_table(u'annotation_direction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('direction', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal(u'annotation', ['Direction'])

        # Adding model 'Stoichiometry'
        db.create_table(u'annotation_stoichiometry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('metabolite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Metabolite'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
            ('compartment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Compartment'], null=True, blank=True)),
            ('stoichiometry', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'annotation', ['Stoichiometry'])

        # Adding model 'Metabolic_model'
        db.create_table(u'annotation_metabolic_model', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Source'])),
            ('reaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Reaction'])),
            ('direction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotation.Direction'])),
        ))
        db.send_create_signal(u'annotation', ['Metabolic_model'])


    def backwards(self, orm):
        # Deleting model 'Source'
        db.delete_table(u'annotation_source')

        # Deleting model 'Gene'
        db.delete_table(u'annotation_gene')

        # Deleting model 'Enzyme'
        db.delete_table(u'annotation_enzyme')

        # Removing M2M table for field genes on 'Enzyme'
        db.delete_table(db.shorten_name(u'annotation_enzyme_genes'))

        # Deleting model 'Reaction'
        db.delete_table(u'annotation_reaction')

        # Deleting model 'Reaction_synonym'
        db.delete_table(u'annotation_reaction_synonym')

        # Deleting model 'GO'
        db.delete_table(u'annotation_go')

        # Deleting model 'EC'
        db.delete_table(u'annotation_ec')

        # Deleting model 'Evidence'
        db.delete_table(u'annotation_evidence')

        # Deleting model 'FFPred'
        db.delete_table(u'annotation_ffpred')

        # Deleting model 'NCBI'
        db.delete_table(u'annotation_ncbi')

        # Deleting model 'Catalyst'
        db.delete_table(u'annotation_catalyst')

        # Deleting model 'Catalyst_ec'
        db.delete_table(u'annotation_catalyst_ec')

        # Deleting model 'Catalyst_go'
        db.delete_table(u'annotation_catalyst_go')

        # Deleting model 'EC_Reaction'
        db.delete_table(u'annotation_ec_reaction')

        # Deleting model 'GO_Reaction'
        db.delete_table(u'annotation_go_reaction')

        # Deleting model 'GO2EC'
        db.delete_table(u'annotation_go2ec')

        # Deleting model 'MTG_cog_result'
        db.delete_table(u'annotation_mtg_cog_result')

        # Deleting model 'FFPred_result'
        db.delete_table(u'annotation_ffpred_result')

        # Deleting model 'FFPred_prediction'
        db.delete_table(u'annotation_ffpred_prediction')

        # Deleting model 'Profunc_result'
        db.delete_table(u'annotation_profunc_result')

        # Deleting model 'Profunc_prediction'
        db.delete_table(u'annotation_profunc_prediction')

        # Deleting model 'Profunc_prediction2'
        db.delete_table(u'annotation_profunc_prediction2')

        # Deleting model 'Eficaz_result'
        db.delete_table(u'annotation_eficaz_result')

        # Deleting model 'Eficaz_prediction'
        db.delete_table(u'annotation_eficaz_prediction')

        # Deleting model 'Iah991_prediction'
        db.delete_table(u'annotation_iah991_prediction')

        # Deleting model 'Metabolite'
        db.delete_table(u'annotation_metabolite')

        # Deleting model 'Metabolite_synonym'
        db.delete_table(u'annotation_metabolite_synonym')

        # Deleting model 'Compartment'
        db.delete_table(u'annotation_compartment')

        # Deleting model 'Direction'
        db.delete_table(u'annotation_direction')

        # Deleting model 'Stoichiometry'
        db.delete_table(u'annotation_stoichiometry')

        # Deleting model 'Metabolic_model'
        db.delete_table(u'annotation_metabolic_model')


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
            'metabolite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Metabolite']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
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
            'enzymes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['annotation.Enzyme']", 'through': u"orm['annotation.Catalyst']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']", 'null': 'True', 'blank': 'True'})
        },
        u'annotation.reaction_synonym': {
            'Meta': {'object_name': 'Reaction_synonym'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'annotation.source': {
            'Meta': {'object_name': 'Source'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        },
        u'annotation.stoichiometry': {
            'Meta': {'object_name': 'Stoichiometry'},
            'compartment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Compartment']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metabolite': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Metabolite']"}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Reaction']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['annotation.Source']"}),
            'stoichiometry': ('django.db.models.fields.FloatField', [], {})
        }
    }

    complete_apps = ['annotation']