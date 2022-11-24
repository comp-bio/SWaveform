import React from 'react';
import axios from 'axios';

const icon = (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-download" viewBox="0 0 16 16">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
);

const description = (
    <div className={'part'}>
        <h2 className="h2">Explanation for the charts:</h2>
        <div className="lead">
            <ul>
                <li>The large image on the left shows a graph of the signals after SAX transformation, for each type of structural variation.</li>
                <li>To the right of the image there are two clusters for each type of structural variation.</li>
                <li>
                    Each cluster shows its size as a percentage and three images:
                    <ol>
                        <li>Overview of a separate cluster. For each signal of this cluster, the mean (thin blue line) and standard deviation (black bar) are drawn.</li>
                        <li>The second figure shows the signals from the database from which the subsignals included in the motive were extracted. The signal is colored grey, the sub-signals are colored orange</li>
                        <li>All orange subsignals that formed the motif are superimposed on each other without shift. For each position, the average integer value is allocated — this is the final "motif", colored in red</li>
                    </ol>
                </li>
            </ul>
        </div>
    </div>
);

const empty = (
    <div className={'part'}>
        No motifs found for this database.
    </div>
);

class ModelsPageTab extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        return <>111</>
    }
}


class ModelsPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'models': [], 'ds_names': [], 'tab': ''};
        this.gridPlot = this.gridPlot.bind(this);
    }

    componentDidMount() {
        axios({url: `/api/models`, method: 'get'}).then((res) => {
            res.data['tab'] = res.data['ds_names'][0];
            this.setState(res.data);
        });
    }

    gridPlot(name, code, cls) {
        const M = this.state.models[name] ? this.state.models[name].meta[`${code}.${cls}.detail.json`] : false;
        if (!M) return (
            <></>
            // <article className={'cluster empty'} key={code + cls}>
            //     [Cluster removed] {`${code}.${cls}.detail.json`}
            // </article>
        );

        return (
            <article className={'cluster'} key={code + cls}>
                <code className={'part'}>{M.part}, Threshold: {M.threshold.toFixed(2)}</code>
                <img className={'img'} src={`/api/media/${M.cluster_detail}`} alt={'Cluster'} />
                <img className={'img'} src={`/api/media/${M.motif_signal}`} alt={'Motif_signal'} />
                <div className={'img-wrap'}>
                    <img className={'img'} src={`/api/media/${M.motif}`} alt={'Motif'} />
                    <a target={'_blank'} href={`/api/models/mt_${M.code}.${M.cluster_name}.motif`} className={'button'}>{icon} Download</a>
                </div>
            </article>
        );
    }

    render() {
        return (
            <>
                {this.state.ds_names.length ? description : empty}
                <div className={'tabs'}>
                    {this.state.ds_names.map(name => (
                        <div onClick={() => this.setState({'tab': name})}
                             key={name}
                             className={'tab' + (name === this.state.tab ? ' current' : '')}>{name}</div>
                    ))}
                    <div className={'spacer'} />
                </div>
                <div className={'model-items'}>
                    {this.state.ds_names.map(name => {
                        if (name !== this.state.tab) return '';
                        return this.state.models[name].media.map(src => {
                            const code = src.split('.plt.png')[0];
                            return (
                                <div className={'model-item'} key={code}>
                                    <img className={'img-type'} src={`/api/media/${src}`} />
                                    <div className={'m-clusters'}>
                                        {this.gridPlot(name, code, 'A')}
                                        {this.gridPlot(name, code, 'B')}
                                    </div>
                                </div>
                            )
                        })
                    })}
                </div>
            </>
        );
    }
}

export default ModelsPage;
