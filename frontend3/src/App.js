import * as React from 'react';
import { useState, useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';
import screenfull from 'screenfull';
import Container from '@mui/material/Container';
import './App.css';
import ControlIcons from './Components/ControlIcons';
import Dropdown from 'react-dropdown';
import 'react-dropdown/style.css';

import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { RecentActors } from '@mui/icons-material';


function TableMax(props) {
    const [tableData, setTableData] = useState(props.data);

    useEffect(() => {
        setTableData(props.data);
    }, [props.data]);

    // state = {
    //     rows: [
    //         createData('Frozen yoghurt', 159, 6.0, 24, 4.0),
    //         createData('Ice cream sandwich', 237, 9.0, 37, 4.3),
    //         createData('Eclair', 262, 16.0, 24, 6.0),
    //         createData('Cupcake', 305, 3.7, 67, 4.3),
    //         createData('Gingerbread', 356, 16.0, 49, 3.9),
    //     ]
    // }
    // handleUpdateRows(e) {
    //     this.setState({
    //         rows: e.target.value
    //     })
    // }

    return (
        <TableContainer component={Paper}>
            <Table sx={{ minWidth: 650 }} aria-label="simple table">
                <TableHead>
                    <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell align="right">Start</TableCell>
                        <TableCell align="right">End&nbsp;(g)</TableCell>
                        <TableCell align="right">Video Timestamp&nbsp;(g)</TableCell>
                        <TableCell align="right">Status&nbsp;(g)</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {tableData.map((row) => (
                        <TableRow
                            key={row["id"]}
                            sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                        >
                            <TableCell component="th" scope="row">
                                {row["id"]}
                            </TableCell>
                            <TableCell align="right">{row["start"]}</TableCell>
                            <TableCell align="right">{row["end"]}</TableCell>
                            <TableCell align="right">{row["video_timestamp"]}</TableCell>
                            <TableCell align="right">{row["status"]}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}



const format = (seconds) => {
    if (isNaN(seconds)) {
        return '00:00'
    }

    const date = new Date(seconds * 1000);
    const hh = date.getUTCHours();
    const mm = date.getUTCMinutes();
    const ss = date.getUTCSeconds().toString().padStart(2, "0");

    if (hh) {
        return `${hh}:${mm.toString().padStart(2, "0")}:${ss}`
    } else {
        return `${mm}:${ss}`
    }
};

function App() {
    const [playerstate, setPlayerState] = useState({
        playing: true,
        muted: true,
        volume: 0.5,
        playerbackRate: 1.0,
        played: 0,
        seeking: false,
    })


    //Destructure State in other to get the values in it
    const { playing, muted, volume, playerbackRate, played, seeking } = playerstate;
    const playerRef = useRef(null);
    const playerDivRef = useRef(null);

    //This function handles play and pause onchange button
    const handlePlayAndPause = () => {
        setPlayerState({ ...playerstate, playing: !playerstate.playing })
    }

    const handleMuting = () => {
        setPlayerState({ ...playerstate, muted: !playerstate.muted })
    }

    const handleRewind = () => {
        playerRef.current.seekTo(playerRef.current.getCurrentTime() - 10)
    }

    const handleFastForward = () => {
        playerRef.current.seekTo(playerRef.current.getCurrentTime() + 30)
    }

    const handleVolumeChange = (e, newValue) => {
        setPlayerState({ ...playerstate, volume: parseFloat(newValue / 100), muted: newValue === 0 ? true : false, });
    }

    const handleVolumeSeek = (e, newValue) => {
        setPlayerState({ ...playerstate, volume: parseFloat(newValue / 100), muted: newValue === 0 ? true : false, });
    }

    const handlePlayerRate = (rate) => {
        setPlayerState({ ...playerstate, playerbackRate: rate });
    }

    const handleFullScreenMode = () => {
        screenfull.toggle(playerDivRef.current)
    }

    const handlePlayerProgress = (state) => {
        console.log('onProgress', state);
        if (!playerstate.seeking) {
            setPlayerState({ ...playerstate, ...state });
        }
        console.log('afterProgress', state);
    }

    const handlePlayerSeek = (e, newValue) => {
        setPlayerState({ ...playerstate, played: parseFloat(newValue / 100) });
        playerRef.current.seekTo(parseFloat(newValue / 100));
        // console.log(played)
    }

    const handlePlayerMouseSeekDown = (e) => {
        setPlayerState({ ...playerstate, seeking: true });
    }

    const handlePlayerMouseSeekUp = (e, newValue) => {
        setPlayerState({ ...playerstate, seeking: false });
        playerRef.current.seekTo(newValue / 100);
    }
    function createData(id, start, finish, video_timestamp, status) {
        return { "id": id, "start": start, "finish": finish, "video_timestamp": video_timestamp, "status": status };
    }
    

    const currentPlayerTime = playerRef.current ? playerRef.current.getCurrentTime() : '00:00';
    const movieDuration = playerRef.current ? playerRef.current.getDuration() : '00:00';
    const playedTime = format(currentPlayerTime);
    const fullMovieTime = format(movieDuration);
    let objects = []
    let d = {
        "result_json": "https://raw.githubusercontent.com/poul250/netris_construction_equipments_detection/master/frontend2/package.json",
        "objects": {
            "tractor1": {
                "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "type": "tractor",
                "timeline": [
                    {
                        "start": 12,
                        "end": 20,
                        "video_timestamp": 0,
                        "status": "working"
                    },
                    {
                        "start": 20,
                        "end": 100,
                        "video_timestamp": 8,
                        "status": "chilling"
                    }
                ]
            },
            "tractor2": {
                "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "type": "tractor",
                "timeline": [
                    {
                        "start": 5,
                        "end": 40,
                        "video_timestamp": 0,
                        "status": "working"
                    },
                    {
                        "start": 40,
                        "end": 100,
                        "video_timestamp": 35,
                        "status": "chilling"
                    },
                    {
                        "start": 100,
                        "end": 150,
                        "video_timestamp": 95,
                        "status": "working"
                    }
                ]
            }
        }
    }
    let tableData = {}
    for (var [obj_id, value] of Object.entries(d["objects"])) {
        objects.push(obj_id)
        let types = value["type"];
        let urls = value["url"];
        let tables = [];
        let timeline = value["timeline"];
        
        tableData[obj_id] = [];
        let i = 0;
        for (let line of timeline) {
            tableData[obj_id].push(createData(i, line["start"], line["end"], line["video_timestamp"], line["status"]));
            i++;
        }
    }
    console.log(tableData);


    const defaultOption = objects[0];
    const defalutTable = tableData[defaultOption];
    console.log(defalutTable);
    let newData = defalutTable;
    const changeTableCont = (e) => {
        newData = tableData[e]
    }
    return (
        <>
            <header className='header__section'>
                <p className='header__text'>Build a Video Player - Tutorial</p>
            </header>
            <Container maxWidth="md">
                <div className='playerDiv' ref={playerDivRef}>
                    <ReactPlayer width={'100%'} height='100%'
                        ref={playerRef}
                        url="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"
                        playing={playing}
                        volume={volume}
                        playbackRate={playerbackRate}
                        onProgress={handlePlayerProgress}
                        muted={muted} />

                    <ControlIcons
                        key={volume.toString()}
                        playandpause={handlePlayAndPause}
                        playing={playing}
                        rewind={handleRewind}
                        fastForward={handleFastForward}
                        muting={handleMuting}
                        muted={muted}
                        volumeChange={handleVolumeChange}
                        volumeSeek={handleVolumeSeek}
                        volume={volume}
                        playerbackRate={playerbackRate}
                        playRate={handlePlayerRate}
                        fullScreenMode={handleFullScreenMode}
                        played={played}
                        onSeek={handlePlayerSeek}
                        onSeekMouseUp={handlePlayerMouseSeekUp}
                        onSeekMouseDown={handlePlayerMouseSeekDown}
                        playedTime={playedTime}
                        fullMovieTime={fullMovieTime}
                        seeking={seeking}
                    />
                </div>
                <div>
                    <Dropdown options={objects} value={defaultOption} onChange={changeTableCont} placeholder="Select an option" />
                </div>
                <div><TableMax data = {defalutTable} newData={newData}/></div>
            </Container>
        </>
    );
}

export default App;
