import React, { useState, Component } from 'react'
import ReactDOM from 'react-dom'

// Import React FilePond
import { FilePond, registerPlugin } from "react-filepond";

// Import FilePond styles
import "filepond/dist/filepond.min.css";

// Import the Image EXIF Orientation and Image Preview plugins
// Note: These need to be installed separately
import FilePondPluginImageExifOrientation from "filepond-plugin-image-exif-orientation";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import "filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css";

// Register the plugins
registerPlugin(FilePondPluginImageExifOrientation, FilePondPluginImagePreview);

// Our app
class Pond extends Component {
    constructor(props) {
        super(props);

        this.state = {
            // Set initial files, type 'local' means this is a file
            // that has already been uploaded to the server (see docs)
            files: [
            ]
        };
    }

    handleInit() {
        console.log("FilePond instance has initialised", this.pond);
    }

    render() {
        console.log(this.state.files)
        return (
            <div className="Pond">
                <FilePond class="Pondex"
                    ref={ref => (this.pond = ref)}
                    headers={
                        {"Access-Control-Allow-Origin": "*"}
                    }
                    files={this.state.files}
                    allowMultiple={true}
                    allowReorder={true}
                    maxFiles={3}
                    server="http://192.168.130.131:8000/upload"
                    name="files" /* sets the file input name, it's filepond by default */
                    oninit={() => this.handleInit()}
                    onupdatefiles={fileItems => {
                        // Set currently active file objects to this.state
                        this.setState({
                            files: fileItems.map(fileItem => fileItem.file)
                        });
                    }}
                />
            </div>
        );
    }
}

export default Pond;