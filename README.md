# Project Overview:

InspirAItion is an innovative AI project that utilizes cutting-edge machine learning technologies to generate and explore artistic images. Users can experience various artistic styles and create unique works. This project was developed by the 6th team of the 3rd team project of MS AI School 5th.

## Key Features:

### AI-Based Image Generation:
Generates images in various artistic styles using advanced AI models.
Allows users to fine-tune prompts, models, and parameters to achieve desired effects.
### Artistic Style Application:
Enables users to experience diverse artistic styles.
Allows users to apply specific artistic styles to their images or create new styles.
### Art Community and Artwork Sharing:
Allows users to share and communicate with others about generated artwork.
Provides a gallery for users to view and be inspired by various artworks.
### Additional Features:
Leverages ComfyUI workflows for upscaling and outpainting.
Upscaling is a technique that enlarges low-resolution images to high-resolution, and outpainting extends image boundaries to create new areas.
### AI Curation:
Provides Curation about generated images by selected style.


# inspirAItion Project

Welcome to the inspirAItion project! This project is designed for the 6th team of the 3rd team project of MS AI School 5th.

## Getting Started

These instructions will help you get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

To run Django locally, you'll need the following:

1. **Python** (version 3.8 or higher) installed on your machine.
2. **PostgreSQL** installed and configured on your local environment.
3. Install dependencies via `pip` using the `requirements.txt` file.
   - Example: `pip install -r requirements.txt`
4. You may have **Node.js** and **npm** installed to handle front-end dependencies if needed.
5. You may also need to have **Virtualenv** installed to manage the virtual environment for the project.

### Installing

Step-by-step instructions to get the development environment up and running:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/yourrepository.git
   ```
2. Navigate into the project directory:
   ```bash
   cd yourrepository
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Mac/Linux
   .\venv\Scripts\activate   # For Windows
   ```
4. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up your PostgreSQL database and configure it in your Django settings.
6. Run Django **migrations**:
   ```bash
   python manage.py makemigrations
   ```
7. Run the migrations to set up your **database**:
   ```bash
   python manage.py migrate
   ```
8. Run the Django **server**:
   ```bash
   python manage.py runserver
   ```    

## Running the tests

Explain how to run the automated tests for this system. You can use Django’s test framework by running:

```bash
python manage.py test
```

## Deployment

For deploying this project on a live system, you can follow the steps based on the platform you're using, such as Heroku, AWS, or any other cloud service. Ensure to configure the database and environment variables properly.

## Built With

* **Django** - Web framework used
* **PostgreSQL** - Database used
* **Bootstrap 5** - Front-end framework used
* **HTML, CSS, JavaScript** - Front-end technologies
* **Python** - Programming language

## Contributing

Please read [cooldevsmart's readme.md](https://github.com/cooldevsmart) for details on our code of conduct, and the process for submitting pull requests.

## Authors

* **cooldevsmart** - Initial work
* **FaithCoderLab** - Back-End, Database
* **jjaayy2222** - Front-End
* **bongs1001** - AI Service

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

* Special thanks to our team members for all the help and inspiration.
* Thanks to everyone whose code was used.
