provider "aws" {
  region = "ap-south-1"
}

resource "aws_instance" "ec2-instance" {
  ami           = "ami-0c55b31ad2299a701"
  instance_type = "t2.micro"
  tags = {
    Name = "ec2-instance"
  }
}