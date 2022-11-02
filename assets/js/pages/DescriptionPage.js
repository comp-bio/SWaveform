import React from 'react'
import { examples, schema, download } from '../components/helpers.js'
import Histogram from "../components/Histogram";
import Signal from "../components/Signal";
import axios from "axios";
import d3 from "d3";

const icon = (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-download" viewBox="0 0 16 16">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
);

class DescriptionPage extends React.Component {
    constructor(props) {
        super(props);
        this.examples = examples();
        this.schema = schema();
        this.state = {'tab': 'Python'};
        // console.log('overview', overview);
    }

    componentDidMount() {
        axios({url: `/api/overview`, method: 'get'}).then((res) => {
            this.setState({'overview': res.data});
        });
    }

    renderOverview()
    {
        let overview = this.state.overview;
        return (
            <>
                <h4 className={'h4'}>Total signals in database:</h4>
                <div className={'items'}><code>{overview.total.toLocaleString()}</code></div>
                <div className={'dataset-groups'}>
                    {Object.keys(overview['ds']).map(ds => {
                        const d = overview['ds'][ds];
                        return (
                            <div className={'dataset-group'} key={ds}>
                                <h4 className={'h4'}>Dataset: <strong>{ds}</strong></h4>
                                <table>
                                    <thead><tr><th>Type of SV &rarr;</th>{Object.keys(d.types).map(type => <th key={type}>{type}</th>)}</tr></thead>
                                    <tbody>
                                    {[['Left', 'L'], ['Right', 'R'], ['BP', 'BP']].map(k =>
                                        <tr key={k}>
                                            <td><span className={`tag side-${k[1]}`}>{k[1]}</span> {k[0]}:</td>
                                            {Object.keys(d.types).map(type => {
                                                let s = 0;
                                                Object.keys(d.types[type]).map(p => {
                                                    if (d.stat[p][type][k[1]]) s += d.stat[p][type][k[1]].count;
                                                })
                                                return <td key={type}>{s}</td>;
                                            })}
                                        </tr>
                                    )}
                                    <tr>
                                        <td><strong>Total:</strong></td>
                                        {Object.keys(d.types).map(type => {
                                            let s = Object.values(d.types[type]).reduce((a, curr) => a + curr)
                                            return <td key={type}>{s}</td>;
                                        })}
                                    </tr>
                                    </tbody>
                                </table>

                                <table>
                                    <thead><tr><th>Population (samples)</th>{Object.keys(d.types).map(type => <th key={type}>{type}</th>)}</tr></thead>
                                    <tbody>
                                    {Object.keys(d.populations).map((p_name, r) => (
                                        <tr key={r}>
                                            <td>{p_name} ({d.populations[p_name]})</td>
                                            {Object.keys(d.types).map(type => {
                                                const stat = d.stat[p_name][type];
                                                return (
                                                    <td className={'data'} key={type}>
                                                        <div className={'histogram-wrapper'}>
                                                            <p className={'helper'}>Coverage histogram:</p>
                                                            <Histogram obj={stat} />
                                                            <div className={'col head'}><span>Side</span><span>Mean</span><span>Count</span></div>
                                                            {Object.keys(stat).map(side => (
                                                                <div className={'col'} key={side}>
                                                                    <span className={`side-${side}`}><b>{side}</b></span>
                                                                    <span>{stat[side].mean.toFixed(2)}</span>
                                                                    <span>{stat[side].count}</span>
                                                                </div>
                                                            ))}
                                                            <div className={'col footer'}><span className={'w66'}>Total</span><span>{d.types[type][p_name]}</span></div>
                                                        </div>
                                                    </td>
                                                );
                                            })}

                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            </div>
                        );
                    })}
                </div>
            </>
        );

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

                <h2 className="h2">
                    <span>Schema</span>
                    <div className={'group'}>
                        <button onClick={() => { download('schema.json', this.schema.documents) }} className={'button'}>{icon} JSON</button>
                        <button onClick={() => { download('schema.sql', this.schema.sqlite, 'application/octet-stream') }} className={'button'}>{icon} SQLite</button>
                    </div>
                </h2>

                <div className={'part tables'}>
                    {this.schema.compact.map((table, k) => (
                        <div key={k} className="col">
                            <h4 className="h4">Table: <code>{table.name}</code></h4>
                            <table>
                                <thead><tr><th>Column</th><th>Description</th></tr></thead>
                                <tbody>
                                {table.columns.map((row,r) => (
                                    <tr key={r}>
                                        <td>{row.name} <code>{row.type.datatype}</code></td>
                                        <td>{row.options.comment}</td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    ))}
                </div>

                <h2 className="h2">
                    <span>Code examples</span>
                    <div className={'group tabs'}>
                        {['Python', 'PHP', 'R'].map(lang => (
                            <button className={`button ${this.state['tab'] === lang ? 'active' : ''}`}
                                    onClick={() => this.setState({'tab': lang})} key={lang}>{lang}</button>
                        ))}
                    </div>
                </h2>
                <div className={'part'}>
                    <h4 className="h4">{this.state['tab']}</h4>
                    <div className={'code'} dangerouslySetInnerHTML={{ __html: this.examples[this.state['tab']] }} />
                </div>

                <h2 className="h2">Statistics</h2>
                <div className={'part stat'}>
                    {(this.state.overview ? this.renderOverview() : '')}
                </div>
            </div>
        );
    }
}

export default DescriptionPage;
