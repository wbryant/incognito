# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Cogzyme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('cogs', models.ManyToManyField(to='cogzymes.Cog')),
            ],
        ),
        migrations.CreateModel(
            name='Enzyme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2500)),
                ('cogzyme', models.ForeignKey(related_name='cog_enzymes', default=None, blank=True, to='cogzymes.Cogzyme', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Enzyme_type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(unique=True, max_length=40)),
                ('description', models.CharField(default=b'', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locus_tag', models.CharField(max_length=100)),
                ('cogs', models.ManyToManyField(to='cogzymes.Cog')),
            ],
        ),
        migrations.CreateModel(
            name='Organism',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('taxonomy_id', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Reaction_pred',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'unk', max_length=3, choices=[(b'unk', b'Unknown'), (b'mod', b'Model'), (b'sus', b'Suspect'), (b'hid', b'Hidden')])),
                ('status', models.CharField(default=b'add', max_length=3, choices=[(b'add', b'add'), (b'rem', b'remove')])),
                ('num_enzymes', models.IntegerField()),
                ('cogzyme', models.ForeignKey(default=None, blank=True, to='cogzymes.Cogzyme', null=True)),
                ('dev_model', models.ForeignKey(related_name='dev_model_preds', to='annotation.Source')),
                ('enzyme_type', models.ForeignKey(default=None, blank=True, to='cogzymes.Enzyme_type', null=True)),
                ('reaction', models.ForeignKey(to='annotation.Model_reaction')),
                ('ref_model', models.ForeignKey(related_name='ref_model_preds', to='annotation.Source')),
            ],
        ),
        migrations.AddField(
            model_name='gene',
            name='organism',
            field=models.ForeignKey(to='cogzymes.Organism'),
        ),
        migrations.AddField(
            model_name='enzyme',
            name='genes',
            field=models.ManyToManyField(to='cogzymes.Gene'),
        ),
        migrations.AddField(
            model_name='enzyme',
            name='reactions',
            field=models.ManyToManyField(related_name='cog_enzymes', to='annotation.Model_reaction'),
        ),
        migrations.AddField(
            model_name='enzyme',
            name='source',
            field=models.ForeignKey(related_name='cog_enzymes', to='annotation.Source'),
        ),
        migrations.AddField(
            model_name='enzyme',
            name='type',
            field=models.ForeignKey(to='cogzymes.Enzyme_type'),
        ),
        migrations.AlterUniqueTogether(
            name='gene',
            unique_together=set([('locus_tag', 'organism')]),
        ),
    ]
