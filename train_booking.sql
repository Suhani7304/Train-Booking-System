CREATE DATABASE TrainBookingDB;
USE TrainBookingDB;

CREATE TABLE train (
    ID INT PRIMARY KEY, 
	TrainID INT,
    TrainName VARCHAR(100),
    Source VARCHAR(100),
    Destination VARCHAR(100),
    ArrivalTime TIME,
    DepartureTime TIME,
    Price INT,
    FOREIGN KEY (TrainID) REFERENCES Route(TrainID)
);
select * from train;
CREATE TABLE Route (
    TrainID INT PRIMARY KEY,
    Route VARCHAR(1000)
);

CREATE TABLE Seats (
    SeatID INT PRIMARY KEY,
    TrainID INT,
    SeatType VARCHAR(50),
    TotalSeats INT,
    FOREIGN KEY (TrainID) REFERENCES Route(TrainID)
);

CREATE TABLE Passenger (
    PassengerID INT PRIMARY KEY AUTO_INCREMENT, # auto increment automatically assigns unique id to each passenger starting from 1 and incrementing
    PassengerName VARCHAR(100),
    Age INT,
    Gender VARCHAR(10),
    Email VARCHAR(100),
    Password VARCHAR(50)
);

CREATE TABLE Booking (
    BookingID INT PRIMARY KEY AUTO_INCREMENT,
    PassengerID INT,
    TrainID INT,
    SeatType VARCHAR(50),
    TravelDate DATE,
    Source VARCHAR(100),
    Destination VARCHAR(100),
    BookingTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Price INT,
    Status VARCHAR(25),
    FOREIGN KEY (PassengerID) REFERENCES Passenger(PassengerID),
    FOREIGN KEY (TrainID) REFERENCES Route(TrainID)
);

CREATE TABLE SeatAvailability (
    AvailabilityID INT PRIMARY KEY AUTO_INCREMENT,
    SeatID INT,
    TravelDate DATE,
    LeftSeats INT,
	Source VARCHAR(100),
    Destination VARCHAR(100),
    FOREIGN KEY (SeatID) REFERENCES Seats(SeatID)
);

CREATE TABLE Admin (
    ID INT,
    UserName VARCHAR(100),
    Age INT,
    Email VARCHAR(100),
    PhoneNumber VARCHAR(15),
    Password VARCHAR(50)
);



select * from Booking;
