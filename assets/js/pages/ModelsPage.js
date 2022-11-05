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
        Для этой базы данных не было найдено мотивов.
    </div>
);

class ModelsPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'models': [], 'meta': [], 'hmm': false, 'title': false};
        this.gridPlot = this.gridPlot.bind(this);
    }

    componentDidMount() {
        axios({url: `/api/models`, method: 'get'}).then((res) => {
            this.setState(res.data);
            res.data.meta.map(src => {
                this.setState({[`src:${src}`]: 'loading'})
                axios({url: `/api/models/${src}`, method: 'get'}).then((res) => {
                    this.setState({[`src:${src}`]: res.data})
                    // console.log('>>>', this.state);
                });
            });
        });
    }

    gridPlot(code, cls) {
        const C = this.state[`src:detail_${code}.${cls}.json`] || null;
        // console.log('>>>', this.state);
        if (C === 'loading') return (
            <article className={'cluster empty'} key={code + cls}>
                [loading]
            </article>
        );
        if (!C) return (
            <article className={'cluster empty'} key={code + cls}>
                [Cluster removed] {`src:detail_${code}.${cls}.json`}
            </article>
        );

        return (
            <article className={'cluster'} key={code + cls}>
                <code className={'part'}>{C.part}</code>
                <img className={'img'} src={`data:image/png;base64,${C.cluster_detail}`}  alt={'Cluster'} />
                <img className={'img'} src={`data:image/png;base64,${C.motif_signal}`}  alt={'Motif_signal'} />
                <div className={'img-wrap'}>
                    <img className={'img'} src={`data:image/png;base64,${C.motif}`}  alt={'Motif'} />
                    <a target={'_blank'} href={`/api/models/mt_${C.code}.${C.cluster_name}.motif`} className={'button'}>{icon} Download</a>
                </div>
            </article>
        );
    }



    render() {
        // console.log('this.state.models', this.state.models);
        return (
            <>
                {this.state.models.length ? description : empty}
                <div className={'model-items'}>
                    {this.state.models.map(src => {
                        const code = src.split('.plt.png')[0];
                        return (
                            <div className={'model-item'} key={code}>
                                <img className={'img-type'} src={`/api/media/${src}`} />
                                <div className={'m-clusters'}>
                                    {this.gridPlot(code,'A')}
                                    {this.gridPlot(code,'B')}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </>
        );
    }
}

export default ModelsPage;
