# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Catalyst',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Catalyst_ec',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Catalyst_go',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cogzyme_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gpr', models.CharField(max_length=1000)),
                ('cog_field', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Combfunc_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('combfunc_score', models.FloatField()),
                ('num_predictions_go', models.IntegerField()),
                ('num_predictions_gene', models.IntegerField()),
                ('num_predictions_reaction', models.IntegerField()),
                ('total_score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Combfunc_result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Compartment',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Direction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('direction', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='EC',
            fields=[
                ('number', models.CharField(max_length=20, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='EC_Reaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Eficaz_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('eficaz_score', models.FloatField()),
                ('num_predictions_ec', models.IntegerField()),
                ('num_predictions_gene', models.IntegerField()),
                ('num_predictions_reaction', models.IntegerField()),
                ('total_score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Eficaz_result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('precision_mean', models.FloatField()),
                ('precision_sd', models.FloatField()),
                ('seq_id_bin', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Enzyme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Evidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='FFPred',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
                ('reliability', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='FFPred_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ffpred_score', models.FloatField()),
                ('num_predictions_go', models.IntegerField()),
                ('num_predictions_gene', models.IntegerField()),
                ('num_predictions_reaction', models.IntegerField()),
                ('total_score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='FFPred_result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
                ('reliability', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('gi', models.IntegerField(serialize=False, primary_key=True)),
                ('locus', models.CharField(max_length=10)),
                ('locus_tag', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=200)),
                ('annotation', models.CharField(max_length=200)),
                ('cog_id', models.CharField(default=None, max_length=7, null=True, blank=True)),
                ('protein_gi', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='GO',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='GO2EC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='GO_Reaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Iah991_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_predictions_gene', models.IntegerField()),
                ('num_predictions_reaction', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Mapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Metabolic_model',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Metabolite',
            fields=[
                ('id', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Metabolite_synonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('synonym', models.CharField(max_length=1000)),
                ('inferred', models.BooleanField(default=False)),
                ('preferred', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Model_metabolite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_id', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=1000)),
                ('curated_db_link', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Model_reaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_id', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=2000)),
                ('gpr', models.CharField(max_length=10000)),
                ('curated_db_link', models.BooleanField(default=True)),
                ('db_mapping_method', models.CharField(default=None, max_length=3, null=True, blank=True, choices=[(b'syn', b'Synonym'), (b'mtp', b'Metprint'), (b'unk', b'Unknown')])),
            ],
        ),
        migrations.CreateModel(
            name='MTG_cog_result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cog_id', models.CharField(max_length=8)),
                ('seed_id', models.CharField(max_length=8)),
                ('type', models.CharField(max_length=1, choices=[(b'i', b'inclusive'), (b'e', b'exclusive')])),
                ('p_value', models.FloatField()),
                ('rank', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Mtg_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='NCBI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Profunc_prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('profunc_score', models.FloatField()),
                ('num_predictions_go', models.IntegerField()),
                ('num_predictions_gene', models.IntegerField()),
                ('num_predictions_reaction', models.IntegerField()),
                ('total_score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Profunc_prediction2',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
                ('total_score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Profunc_result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('balanced', models.BooleanField(default=True)),
                ('reversibility_eqbtr', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Reaction_group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Reaction_synonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('synonym', models.CharField(max_length=1000)),
                ('inferred', models.BooleanField(default=False)),
                ('preferred', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('name', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('reference_model', models.NullBooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Stoichiometry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stoichiometry', models.FloatField()),
                ('compartment', models.ForeignKey(blank=True, to='annotation.Compartment', null=True)),
                ('metabolite', models.ForeignKey(to='annotation.Metabolite')),
                ('reaction', models.ForeignKey(to='annotation.Reaction')),
                ('source', models.ForeignKey(to='annotation.Source')),
            ],
        ),
    ]
