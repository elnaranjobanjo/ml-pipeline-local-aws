resource "aws_ecs_cluster" "training" {
  name = "training-cluster"
}

resource "aws_ecs_task_definition" "training" {
  family                   = "training-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.task_execution.arn

  container_definitions = jsonencode([
    {
      name  = "training"
      image = "${aws_ecr_repository.training.repository_url}:latest"
      essential = true
      environment = [
        { name = "AWS_ENDPOINT_URL", value = "http://localstack:4566" }
      ]
    }
  ])
}

resource "aws_ecs_service" "training" {
  name            = "training-service"
  cluster         = aws_ecs_cluster.training.id
  task_definition = aws_ecs_task_definition.training.arn
  desired_count   = 1
  launch_type     = "FARGATE"
}
