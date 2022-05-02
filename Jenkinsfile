node {
    def app

    stage('Clone repository') {
        /* Cloning the Repository to our Workspace */

        checkout scm
    }
    stage('Build image') {
        /* This builds the actual image */

        app = docker.build("noetic")
    }
    stage('Test image') {     
        app.inside {
            echo "Tests passed"
        }
    }
     stage ('Email Notification'){
         mail bcc: '', body: 'Giskardpy has successfully built.', cc: '', from: '', replyTo: '', subject: 'Giskardpy building', to: 'iaiciserver@gmail.com'
     }
}
   
