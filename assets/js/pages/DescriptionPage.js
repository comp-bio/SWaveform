import React from 'react';
import {overview} from "../components/Plot";
import {schema} from "../components/Schema";
import ex_sql from '../../../data/schema.sql';
import ex_py from '../../../data/example.py';
import ex_php from '../../../data/example.php';
import ex_r from '../../../data/example.R';

import hljs from 'highlight.js/lib/core';
import sql from 'highlight.js/lib/languages/sql';
import python from 'highlight.js/lib/languages/python';
import php from 'highlight.js/lib/languages/php';
import r from 'highlight.js/lib/languages/r';

hljs.registerLanguage('sql', sql);
hljs.registerLanguage('python', python);
hljs.registerLanguage('php', php);
hljs.registerLanguage('r', r);

class DescriptionPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'ex_sql': '', 'ex_php': '', 'ex_py': '', 'ex_r': ''};
    }

    table(data) {
        return (
            <table>
                <thead><tr><th>Column</th><th>Description</th></tr></thead>
                <tbody>{data.map((row,r) => <tr key={r}>{row.map((v,vk) => <td key={vk}>{v}</td>)}</tr>)}</tbody>
            </table>
        );
    }

    iter(name) {
        return Object.keys(overview[name]).map((v, k) => {
            return <div key={k}>{v}: <code>{overview[name][v]}</code></div>;
        });
    }

    componentDidMount() {
        this.setState({
            'ex_sql': hljs.highlight(ex_sql, {language: 'sql', ignoreIllegals: true }).value,
            'ex_py': hljs.highlight(ex_py, {language: 'python', ignoreIllegals: true }).value,
            'ex_php': hljs.highlight(ex_php, {language: 'php', ignoreIllegals: true }).value,
            'ex_r': hljs.highlight(ex_r, {language: 'r', ignoreIllegals: true }).value,
        });
    }

    render() {
        return (
            <div>
                <div className={'part'}>
                    <p className="lead">
                        The coverage signal database contains data on genome coverage in the vicinity of breakpoints of structural variants (table <code>signal</code>).
                        All coverage values are stored without normalization and without compression.
                        For each signal, the database indicates which of the breakpoints of the structural variant was used: left (L) or right (R).
                        For each signal, the database stores information about the sample from which it was received (table <code>target</code>).
                        In the visualization, the breakpoint is located exactly in the center (highlighted with a vertical red line).
                        The horizontal blue line is the average coverage for the sample from which the signal was derived.
                        Data source: Human Genome Diversity Project (HGDP).
                    </p>
                </div>

                <h2 className="h2">Schema</h2>
                <div className={'part tables'}>
                    <div className="col">
                        <h4 className="h4">Tracks with signals, <code>signal</code></h4>
                        {this.table(schema['s'])}
                    </div>
                    <div className="col">
                        <h4 className="h4">Meta information about samples, <code>target</code></h4>
                        {this.table(schema['t'])}
                    </div>
                </div>

                <h2 className="h2">SQL</h2>
                <div className={'part'}>
                    <div className={'code'} dangerouslySetInnerHTML={{ __html: this.state.ex_sql }} />
                </div>

                <h2 className="h2">Usage examples</h2>
                <div className={'part'}>
                    <h4 className="h4">Python</h4>
                    <div className={'code'} dangerouslySetInnerHTML={{ __html: this.state.ex_py }} />

                    <h4 className="h4">PHP</h4>
                    <div className={'code'} dangerouslySetInnerHTML={{ __html: this.state.ex_php }} />

                    <h4 className="h4">R</h4>
                    <div className={'code'} dangerouslySetInnerHTML={{ __html: this.state.ex_r }} />
                </div>

                <h2 className="h2">Statistics</h2>
                <div className={'part stat'}>
                    <h4 className={'h4'}>Total signals:</h4>
                    <div className={'items'}><code>{overview.total.toLocaleString()}</code></div>

                    <h4 className={'h4'}>Number of samples in populations:</h4>
                    <div className={'items'}>{this.iter('populations')}</div>

                    <h4 className={'h4'}>Number of signals grouped by the type of structural variation:</h4>
                    <div className={'items'}>{this.iter('types')}</div>
                </div>
            </div>
        );
    }
}

export default DescriptionPage;
