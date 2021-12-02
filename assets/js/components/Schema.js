
export const schema = {
    's': [
        ['id',        'Primary ID'],
        ['target_id', 'Reference for target primary ID'],
        ['chr',       'Chromosome'],
        ['start',     'Signal start coordinate (-256bp from bp)'],
        ['end',       'End of signal coordinate (+ 256bp from bp)'],
        ['type',      'Structural variation Type'],
        ['side',      'Left, right or center breakpoint of the SV (L, R, C)'],
        ['coverage',  'Coverage values in binary format'],
    ],
    't': [
        ['id',         'Primary ID'],
        ['name',       'Sample name in VCF file'],
        ['file',       '.cram file suffix'],
        ['dataset',    'Name of source database'],
        ['population', 'Population name'],
        ['region',     'Population region'],
        ['sex',        'Sex'],
        ['meancov',    'Average genome coverage for a Sample'],
    ],
};
